import csv
import io
from uuid import UUID

from fastapi import UploadFile
from sqlalchemy.ext.asyncio import AsyncSession

from app.services.classification_pipeline import classify_ticket
from app.services.config_management import get_config_with_relations
from app.services.feedback_learning import store_feedback

TEXT_COLUMN_NAMES = {"text", "ticket", "message", "texte", "content", "description"}


async def parse_csv(file: UploadFile) -> list[dict]:
    content = await file.read()
    text = content.decode("utf-8-sig")

    sample = text[:2048]
    try:
        dialect = csv.Sniffer().sniff(sample, delimiters=",;\t")
    except csv.Error:
        dialect = csv.excel
        dialect.delimiter = ";" if text.count(";") > text.count(",") else ","

    reader = csv.DictReader(io.StringIO(text), dialect=dialect)
    if reader.fieldnames is None:
        return []

    text_col = None
    for col in reader.fieldnames:
        if col.strip().lower() in TEXT_COLUMN_NAMES:
            text_col = col
            break

    if text_col is None:
        text_col = reader.fieldnames[0]

    label_columns = {}
    for col in reader.fieldnames:
        normalized = col.strip().lower()
        if normalized == text_col.strip().lower():
            continue
        label_columns[col] = col.strip()

    rows = []
    for i, row in enumerate(reader):
        ticket_text = (row.get(text_col) or "").strip()
        labels = {}
        for col, name in label_columns.items():
            val = (row.get(col) or "").strip()
            if val:
                labels[name] = val

        rows.append({
            "row_number": i + 2,
            "text": ticket_text,
            "labels": labels,
        })

    return rows


async def import_tickets_from_csv(
    file: UploadFile, config_id: UUID, db: AsyncSession
) -> dict:
    config = await get_config_with_relations(config_id, db)
    rows = await parse_csv(file)

    axis_map = {a.name.lower(): a for a in config.axes}
    cat_maps = {}
    for axis in config.axes:
        cat_maps[axis.name.lower()] = {
            c.name.lower(): c for c in axis.categories
        }

    imported = 0
    skipped = 0
    errors = []

    for row in rows:
        text = row["text"]
        row_num = row["row_number"]

        if not text:
            skipped += 1
            errors.append({"row": row_num, "reason": "texte vide"})
            continue

        if len(text) < 5:
            skipped += 1
            errors.append({"row": row_num, "reason": "texte trop court (< 5 chars)"})
            continue

        try:
            classification = await classify_ticket(text, config, db)

            labels = row.get("labels", {})
            for label_col, label_val in labels.items():
                axis = axis_map.get(label_col.lower())
                if axis is None:
                    continue
                cat_lookup = cat_maps.get(axis.name.lower(), {})
                cat = cat_lookup.get(label_val.lower())
                if cat is None:
                    continue

                await store_feedback(
                    classification_id=classification.id,
                    axis_id=axis.id,
                    corrected_category_id=cat.id,
                    reasoning_feedback="Import CSV ground-truth",
                    feedback_type="corrected",
                    db=db,
                )

            imported += 1
        except Exception as exc:
            errors.append({"row": row_num, "reason": str(exc)})

    return {
        "total_rows": len(rows),
        "imported": imported,
        "skipped": skipped,
        "errors": len(errors) - skipped,
        "error_details": errors[:50],
    }
