from sqlmodel import Session, select, func
from fastapi import HTTPException, BackgroundTasks, Depends
from app.models.model_tables import Question, Account, Manager, RawData
from app.llm import LLMModel
from app.config import logger, settings
from sqlalchemy import text
from app.schemas.schema_pagination import PaginationMeta
from app.schemas.schema_question import QuestionRead, get_random_typed_question_create, MatchElementsExercise
from app.dependencies import get_image_url, get_questions_llm
from typing import Optional
import math
from typing_extensions import Annotated

def _question_to_read(question: Question, base_url: str) -> QuestionRead:
    return QuestionRead(**question.model_dump(), image_url=get_image_url(base_url, question))

async def calculate_embedding_in_background(question: Question, session: Session, embedding_model: LLMModel):
    question = session.get(Question, question.id)
    question.embedding = await embedding_model.embed(str(question.exercise))
    session.add(question)
    session.commit()
    logger.debug(f"Embedding calculated in background for question ID {question.id}")

async def calculate_raw_data_embedding_in_background(raw_data: RawData, account_id: int, session: Session, embedding_model: LLMModel, background_tasks: BackgroundTasks):
    raw_data = session.get(RawData, raw_data.id)
    raw_data.embedding = await embedding_model.embed(raw_data.text)
    session.add(raw_data)
    session.commit()
    logger.debug(f"Embedding calculated in background for raw data ID {raw_data.id}")

    # Check if we can generate a question from raw data
    current_account = session.get(Account, account_id)
    if not current_account:
        logger.warning(f"Account with ID {account_id} not found")
        return
    
    cluster = get_raw_data_cluster(session, current_account)
    if cluster:
        await generate_question_from_raw_data(cluster, current_account.id, session, embedding_model, background_tasks)

async def generate_question_from_raw_data(cluster: list[RawData], account_id: int, session: Session, embedding_model: LLMModel, background_tasks: BackgroundTasks):
    generation_model = get_questions_llm()
    question_generate = get_random_typed_question_create()
    prompt = question_generate.prompt
    prompt += "Données :\n"
    for raw_data in cluster:
        prompt += f"{raw_data.text}\n"
        if raw_data.file_path:
            prompt += f"File: {raw_data.file_path}\n"
    generated_question = await generation_model.generate(prompt, format=question_generate.question_class)
    if generated_question is None:
        logger.warning("No question generated from raw data cluster")
        return
    print(f"Generated question: {generated_question}")
    
    # Convert the exercise object to a dictionary to make it JSON serializable
    if isinstance(generated_question.exercise, MatchElementsExercise):
        exercise_dict = generated_question.exercise.pairs
    else:
        exercise_dict = generated_question.exercise.model_dump() if hasattr(generated_question.exercise, "model_dump") else generated_question.exercise.__dict__
    
    formatted = Question(
        type=question_generate.type,
        category="IA",
        exercise=exercise_dict,
        image_path=generated_question.image_path,
        account_id=account_id,
        created_by=None,
        edited_by=None,
    )
    current_account = session.get(Account, account_id)
    question = create_question(session, formatted, current_account=current_account, embedding_model=embedding_model, background_tasks=background_tasks)
    if question is None:
        logger.warning("Failed to create question from generated data")
        return
    for raw_data in cluster:
        raw_data.used_for_question_generation = question.id
        session.add(raw_data)
    session.commit()
    logger.info(f"Question generated from raw data cluster: {question.id}")

def create_question(session: Session, question: Question, embedding_model: LLMModel, background_tasks: BackgroundTasks, current_manager: Manager = None, current_account: Account = None,) -> Question:
    question.created_by = current_manager.id if current_manager else None
    question.edited_by = current_manager.id if current_manager else None
    question.account_id = current_manager.account_id if current_manager else current_account.id if current_account else None
    session.add(question)
    session.commit()
    session.refresh(question)

    if embedding_model is not None:
        background_tasks.add_task(calculate_embedding_in_background, question, session, embedding_model)

    return question

def read_questions(session: Session, current_account: Account, base_url: str, page: Optional[int] = None, size: Optional[int] = None) -> list[QuestionRead] | tuple[list[QuestionRead], PaginationMeta]:
    base_query = select(Question).join(Account).where(Question.account_id == current_account.id)
    
    # Si pas de pagination demandée, comportement original
    if page is None or size is None:
        questions = session.exec(base_query).all()
        return [_question_to_read(question, base_url) for question in questions]
    
    # Calcul du total et pagination (validations déjà faites dans le router)
    total = session.exec(select(func.count(Question.id)).join(Account).where(Question.account_id == current_account.id)).first()
    pages = math.ceil(total / size) if total > 0 else 1
    
    # Ajustement de la page si trop élevée
    page = min(page, pages)
    
    # Requête paginée
    offset = (page - 1) * size
    questions = session.exec(base_query.offset(offset).limit(size)).all()
    
    return [_question_to_read(question, base_url) for question in questions], PaginationMeta(
        page=page, size=size, total=total, pages=pages
    )

def update_question(session: Session, question_data: Question, current_question: Question, current_manager: Manager, embedding_model: LLMModel, background_tasks: BackgroundTasks) -> Question:
    question_data.edited_by = current_manager.id

    for key, value in question_data.model_dump().items():
        if value is not None:
            setattr(current_question, key, value)
    
    if embedding_model is not None:
        background_tasks.add_task(calculate_embedding_in_background, current_question, session, embedding_model)
    return current_question

def delete_question(session: Session, current_question: Question) -> bool:
    session.delete(current_question)
    session.commit()
    return True

def get_nearest_questions(session: Session, current_question: Question, limit: int = 5) -> list[Question]:
    if current_question.embedding is None:
        raise HTTPException(status_code=503, detail="Question does not have an embedding")

    nearest_questions = session.exec(
        select(Question.exercise)
        .where(Question.account_id == current_question.account_id, Question.id != current_question.id)
        .order_by(Question.embedding.l2_distance(current_question.embedding))
        .limit(limit)
    ).all()

    return nearest_questions

def create_raw_data(session: Session, text: str, current_account: Account, current_manager: Manager, file_path: str = None, filename: str = None, embedding_model: LLMModel = None, background_tasks: BackgroundTasks = None) -> RawData:
    raw_data = RawData(
        account_id=current_account.id,
        text=text,
        created_by=current_manager.id,
        edited_by=current_manager.id,
        file_path=f"{file_path}_{filename}" if file_path and filename else None,
    )
    
    session.add(raw_data)
    session.commit()
    session.refresh(raw_data)

    if file_path and filename:
        raw_data.file_path = f"{file_path}_{str(raw_data.id)}_{filename}"
        session.commit()
    
    if embedding_model is not None and background_tasks is not None:
        background_tasks.add_task(calculate_raw_data_embedding_in_background, raw_data, current_account.id, session, embedding_model, background_tasks)

    return raw_data

def get_raw_data(session: Session, current_account: Account) -> list[RawData]:
    query = select(RawData).where(RawData.account_id == current_account.id)
    result = session.exec(query)
    return result.all()

# function that gets a cluster of 3 raw data next to each other (l2 distance < 0.7)
# Parcours optimisé de la base de données, récupère un cluster non utilisé de raw data
def get_raw_data_cluster(session: Session, current_account: Account, limit: int = 3, l2_threshold: float = 0.8) -> list[RawData]:
    if not settings.llm_enabled:
        logger.warning("LLM is not enabled, cannot get raw data cluster")
        return []

    # New approach: Find the first valid cluster by checking all possible pivots
    sql = text("""
        WITH candidate_pivots AS (
            SELECT rd.id AS pivot_id
            FROM rawdata rd
            WHERE rd.account_id = :account_id
            AND rd.used_for_question_generation IS NULL
            AND rd.embedding IS NOT NULL
        ),
        pivot_with_neighbors AS (
            SELECT 
                cp.pivot_id,
                COUNT(*) AS neighbor_count
            FROM candidate_pivots cp
            JOIN rawdata rd ON TRUE
            WHERE rd.account_id = :account_id
            AND rd.used_for_question_generation IS NULL
            AND rd.embedding IS NOT NULL
            AND rd.id != cp.pivot_id
            AND rd.embedding <-> (SELECT embedding FROM rawdata WHERE id = cp.pivot_id) <= :l2_threshold
            GROUP BY cp.pivot_id
            HAVING COUNT(*) >= :min_neighbors
            ORDER BY neighbor_count DESC
            LIMIT 1
        ),
        best_pivot AS (
            SELECT rd.*
            FROM rawdata rd
            JOIN pivot_with_neighbors pwn ON rd.id = pwn.pivot_id
        ),
        neighbors AS (
            SELECT rd.*
            FROM rawdata rd
            JOIN best_pivot p ON TRUE
            WHERE rd.account_id = :account_id
            AND rd.used_for_question_generation IS NULL
            AND rd.embedding IS NOT NULL
            AND rd.id != p.id
            AND rd.embedding <-> p.embedding <= :l2_threshold
            ORDER BY rd.embedding <-> p.embedding
            LIMIT :limit
        )
        SELECT * FROM best_pivot
        UNION
        SELECT * FROM neighbors
    """)
    result = session.execute(sql, {
        "account_id": current_account.id,
        "limit": limit - 1,
        "l2_threshold": l2_threshold,
        "min_neighbors": limit - 1
    })

    rows = result.fetchall()

    # Vérifier que nous avons trouvé un cluster avec au moins le nombre minimum d'éléments demandés 
    if len(rows) < limit:
        logger.info(f"Aucun cluster adéquat trouvé: {len(rows)} éléments < {limit} demandés")
        return []

    # Convertir les résultats bruts en objets RawData complets
    raw_data_ids = [row.id for row in rows]
    raw_data_objects = session.exec(select(RawData).where(RawData.id.in_(raw_data_ids))).all()
    
    # Calculer les distances L2 pour vérifier la cohérence du cluster à partir du pivot
    if len(raw_data_objects) > 1:
        pivot = raw_data_objects[0]
        for i in range(1, len(raw_data_objects)):
            if pivot.embedding is not None and raw_data_objects[i].embedding is not None:
                distance = session.exec(
                    select(RawData.embedding.l2_distance(pivot.embedding))
                    .where(RawData.id == raw_data_objects[i].id)
                ).first()
                logger.debug(f"Distance L2 entre {pivot.id} et {raw_data_objects[i].id}: {distance}")
                if distance > l2_threshold:
                    logger.warning(f"Distance L2 inattendue > seuil: {distance} > {l2_threshold}")
    
    logger.info(f"Cluster trouvé avec {len(raw_data_objects)} éléments")
    return raw_data_objects