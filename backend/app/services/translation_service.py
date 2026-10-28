import logging
import os
from functools import lru_cache

from dotenv import dotenv_values

try:
    import torch
    from IndicTransToolkit import IndicProcessor
    from transformers import AutoModelForSeq2SeqLM, AutoTokenizer
except ImportError:
    torch = None
    IndicProcessor = None
    AutoModelForSeq2SeqLM = None
    AutoTokenizer = None

try:
    from deep_translator import GoogleTranslator
except ImportError:
    GoogleTranslator = None

from app.services.chat_service import BACKEND_ENV_FILE, ROOT_ENV_FILE

logger = logging.getLogger(__name__)

LANGUAGE_CODES = {
    "English": "eng_Latn",
    "Hindi": "hin_Deva",
    "Telugu": "tel_Telu",
    "Tamil": "tam_Taml",
}


def _configured_setting(name: str, default: str = "") -> str:
    value = os.getenv(name, "").strip()
    if value:
        return value
    for env_file in (BACKEND_ENV_FILE, ROOT_ENV_FILE):
        configured = dotenv_values(env_file).get(name)
        if isinstance(configured, str) and configured.strip():
            return configured.strip()
    return default


INDICTRANS_MODEL_EN_INDIC = _configured_setting(
    "INDICTRANS_MODEL_EN_INDIC",
    "ai4bharat/indictrans2-en-indic-dist-200M",
)
INDICTRANS_MODEL_INDIC_EN = _configured_setting(
    "INDICTRANS_MODEL_INDIC_EN",
    "ai4bharat/indictrans2-indic-en-1B",
)
INDICTRANS_MODEL_INDIC_INDIC = _configured_setting(
    "INDICTRANS_MODEL_INDIC_INDIC",
    "ai4bharat/indictrans2-indic-indic-1B",
)


class TranslationError(Exception):
    pass


def _language_code(language: str) -> str:
    try:
        return LANGUAGE_CODES[language]
    except KeyError as error:
        raise TranslationError(f"Unsupported translation language: {language}") from error


@lru_cache(maxsize=3)
def _load_indictrans_model(model_name: str):
    if not all((torch, IndicProcessor, AutoTokenizer, AutoModelForSeq2SeqLM)):
        raise TranslationError(
            "IndicTrans2 dependencies are not installed. Install backend requirements."
        )

    device = "cuda" if torch.cuda.is_available() else "cpu"
    processor = IndicProcessor(inference=True)
    tokenizer = AutoTokenizer.from_pretrained(model_name, trust_remote_code=True)
    model = AutoModelForSeq2SeqLM.from_pretrained(
        model_name,
        trust_remote_code=True,
    ).to(device)
    model.eval()
    return processor, tokenizer, model, device


def _translate_indictrans(text: str, source: str, target: str) -> str:
    source_code = _language_code(source)
    target_code = _language_code(target)
    if source_code == target_code:
        return text

    if source_code == "eng_Latn":
        model_name = INDICTRANS_MODEL_EN_INDIC
    elif target_code == "eng_Latn":
        model_name = INDICTRANS_MODEL_INDIC_EN
    else:
        model_name = INDICTRANS_MODEL_INDIC_INDIC

    processor, tokenizer, model, device = _load_indictrans_model(model_name)
    batch = processor.preprocess_batch(
        [text],
        src_lang=source_code,
        tgt_lang=target_code,
        visualize=False,
    )
    inputs = tokenizer(
        batch,
        padding="longest",
        truncation=True,
        max_length=256,
        return_tensors="pt",
    ).to(device)
    with torch.inference_mode():
        outputs = model.generate(
            **inputs,
            num_beams=5,
            num_return_sequences=1,
            max_length=256,
        )
    decoded = tokenizer.batch_decode(
        outputs,
        skip_special_tokens=True,
        clean_up_tokenization_spaces=True,
    )
    return processor.postprocess_batch(decoded, lang=target_code)[0]


def _translate_google(text: str, source: str, target: str) -> str:
    if GoogleTranslator is None:
        raise TranslationError(
            "Google Translate fallback is unavailable. Install backend requirements."
        )
    source_code = "auto" if source == "English" else _language_code(source).split("_")[0]
    target_code = _language_code(target).split("_")[0]
    return GoogleTranslator(source=source_code, target=target_code).translate(text)


def translate_text(text: str, source: str, target: str) -> tuple[str, str]:
    if not text.strip():
        raise TranslationError("Translation text must not be blank.")
    if source == target:
        return text, "none"

    try:
        return _translate_indictrans(text, source, target), "indictrans2"
    except Exception as error:
        logger.warning(
            "IndicTrans2 translation unavailable (%s); using Google Translate fallback",
            type(error).__name__,
        )

    try:
        return _translate_google(text, source, target), "google_translate"
    except Exception as error:
        logger.warning("Google Translate fallback failed (%s)", type(error).__name__)
        raise TranslationError(
            "Translation is unavailable. Configure IndicTrans2 or check the "
            "Google Translate fallback connection."
        ) from error
