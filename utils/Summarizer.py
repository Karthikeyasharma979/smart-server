from openai import OpenAI
import os
import logging
import re
import difflib

logger = logging.getLogger(__name__)

_client = None

# Prefer newer models first and gracefully fall back if unavailable for a key/account.
MODEL_CANDIDATES = [
    "openai/gpt-4o-mini",
    "meta/Llama-3.3-70B-Instruct",
    "cohere/Cohere-command-r-plus-08-2024",
]

def get_client():
    global _client
    if _client is None:
        github_token = os.getenv("GITHUB_TOKEN")
        if not github_token:
            logger.warning("GITHUB_TOKEN not found in environment variables.")
        _client = OpenAI(
            base_url="https://models.github.ai/inference",
            api_key=github_token,
        )
    return _client


def _create_completion_with_fallback(client, messages, max_tokens):
    last_error = None

    for model_name in MODEL_CANDIDATES:
        try:
            return client.chat.completions.create(
                model=model_name,
                messages=messages,
                max_tokens=max_tokens,
            )
        except Exception as e:
            # Continue only for model-availability failures, otherwise bubble up immediately.
            error_text = str(e).lower()
            if (
                "not found" in error_text
                or "404" in error_text
                or "not supported" in error_text
                or "429" in error_text
                or "rate limit" in error_text
                or "500" in error_text
                or "502" in error_text
                or "503" in error_text
                or "504" in error_text
            ):
                logger.warning(f"Model '{model_name}' failed with transient/unavailable error, trying next candidate.")
                last_error = e
                continue
            raise

    # If all model candidates failed with 404/not-supported, raise the last seen error.
    raise last_error if last_error else RuntimeError("No compatible Gemini model was available.")


def _word_count(text: str) -> int:
    return len(re.findall(r"\b\w+\b", text or ""))


def _looks_incomplete(text: str) -> bool:
    cleaned = (text or "").strip()
    if not cleaned:
        return True
    if len(cleaned) < 40:
        return True
    if cleaned.endswith(",") or cleaned.endswith(";") or cleaned.endswith(":"):
        return True
    return False


def _has_excessive_verbatim_overlap(source_text: str, summary_text: str, ngram_size: int = 9) -> bool:
    source = re.sub(r"\s+", " ", (source_text or "").strip().lower())
    summary = re.sub(r"\s+", " ", (summary_text or "").strip().lower())
    if not source or not summary:
        return False

    src_words = source.split()
    sum_words = summary.split()
    if len(sum_words) < ngram_size:
        return False

    src_ngrams = {" ".join(src_words[i:i + ngram_size]) for i in range(len(src_words) - ngram_size + 1)}
    for i in range(len(sum_words) - ngram_size + 1):
        if " ".join(sum_words[i:i + ngram_size]) in src_ngrams:
            return True
    return False


def _is_near_copy(source_text: str, summary_text: str) -> bool:
    source = re.sub(r"\s+", " ", (source_text or "").strip().lower())
    summary = re.sub(r"\s+", " ", (summary_text or "").strip().lower())
    if not source or not summary:
        return False

    if source == summary:
        return True

    return difflib.SequenceMatcher(None, source, summary).ratio() >= 0.88


def _effective_min_words(target_min_words: int, source_text: str) -> int:
    source_words = _word_count(source_text)
    if source_words <= 0:
        return target_min_words

    # Never force a summary close to or longer than the source.
    source_based_cap = max(20, int(source_words * 0.65))
    return min(target_min_words, source_based_cap)


def _extractive_fallback_summary(source_text: str, min_words: int, max_words: int, is_bullets: bool) -> str:
    # Deterministic compressive fallback: select a subset of salient sentences.
    sentences = [s.strip() for s in re.split(r"(?<=[.!?])\s+", source_text or "") if s.strip()]
    if not sentences:
        return (source_text or "").strip()

    source_word_count = _word_count(source_text)
    # Keep fallback comfortably shorter than source to avoid echoing input text.
    compression_cap = max(20, int(source_word_count * 0.6))
    adjusted_max_words = min(max_words, compression_cap)

    if len(sentences) == 1:
        words = sentences[0].split()
        target_words = max(min_words, min(adjusted_max_words, max(20, int(len(words) * 0.7))))
        condensed = " ".join(words[:target_words])
        if is_bullets:
            return f"• {condensed}"
        return condensed

    selected = []
    word_total = 0

    # Prefer lead, key middle, and closing sentences for a more summary-like fallback.
    candidate_indices = [0]
    if len(sentences) > 2:
        candidate_indices.append(len(sentences) // 2)
    if len(sentences) > 1:
        candidate_indices.append(len(sentences) - 1)

    seen_indices = set()
    for idx in candidate_indices + list(range(len(sentences))):
        if idx in seen_indices:
            continue
        seen_indices.add(idx)
        sentence = sentences[idx]
        sentence_words = _word_count(sentence)
        if sentence_words == 0:
            continue
        if word_total >= adjusted_max_words:
            break
        if word_total + sentence_words > adjusted_max_words and selected:
            continue
        selected.append(sentence)
        word_total += sentence_words

    # Guarantee minimum content when first pass is too short.
    if word_total < min_words:
        for sentence in sentences:
            if sentence in selected:
                continue
            sentence_words = _word_count(sentence)
            if sentence_words == 0:
                continue
            if word_total + sentence_words > adjusted_max_words and selected:
                continue
            selected.append(sentence)
            word_total += sentence_words
            if word_total >= min_words:
                break

    if is_bullets:
        return "\n".join(f"• {s}" for s in selected)

    return " ".join(selected)

def summary(text: str, length="medium", format_type="paragraph"):
    client = get_client()

    # Normalize unsupported values so the behavior is predictable.
    normalized_length = (length or "medium").strip().lower()
    if normalized_length not in {"short", "medium", "long"}:
        normalized_length = "medium"

    normalized_format = (format_type or "paragraph").strip().lower()
    is_bullets = "bullet" in normalized_format or "point" in normalized_format

    length_constraints = {
        "short": {
            "words": "60-90 words",
            "bullets": "3-5 concise bullet points",
            "paragraphs": "exactly 1 concise paragraph with 2-4 full sentences",
            "max_tokens": 180,
            "min_words": 55,
        },
        "medium": {
            "words": "90-140 words",
            "bullets": "5-7 bullet points",
            "paragraphs": "1-2 paragraphs",
            "max_tokens": 280,
            "min_words": 85,
        },
        "long": {
            "words": "180-260 words",
            "bullets": "8-12 bullet points",
            "paragraphs": "2-3 detailed paragraphs",
            "max_tokens": 520,
            "min_words": 170,
        },
    }

    selected = length_constraints[normalized_length]
    format_instruction = (
        "a bulleted list. Put each bullet on a new line and start with '•'."
        if is_bullets
        else "well-structured paragraph text"
    )
    structure_instruction = selected["bullets"] if is_bullets else selected["paragraphs"]

    prompt = (
        f"You are an expert summarization assistant. Your task is to synthesize the core ideas and critical details from the provided text.\n\n"
        f"Target Length: {normalized_length.upper()} summary. This is a strict requirement.\n"
        f"Word Budget: {selected['words']}.\n"
        f"Required Structure: {structure_instruction}.\n"
        f"Output Format: {format_instruction}\n\n"
        f"Guidelines (strict):\n"
        f"- Do not output a medium-length summary when SHORT or LONG is requested.\n"
        f"- Stay inside the requested word budget as closely as possible.\n"
        f"- Every sentence must be complete and grammatically correct. No sentence fragments.\n"
        f"- The output must be meaningful and self-contained; never return a partial phrase.\n"
        f"- Use clear paraphrasing in your own words; do not copy source lines verbatim.\n"
        f"- Do not reuse long phrases from the source (avoid copying 8+ consecutive words).\n"
        f"- Merge related points into concise insights instead of sentence-by-sentence copying.\n"
        f"- Cover: main topic, key arguments/facts, and the final takeaway/implication.\n"
        f"- Ensure the summary contains no hallucinations or external information.\n"
        f"- Maintain the original context and overall tone of the text.\n"
        f"- Return purely the requested summary without any conversational filler, meta-talk, or introductions.\n\n"
        f"Text to Summarize:\n"
        f"\"\"\"{text}\"\"\""
    )

    try:
        messages = [
            {
                "role": "user",
                "content": prompt
            }
        ]

        completion = _create_completion_with_fallback(
            client=client,
            messages=messages,
            max_tokens=selected["max_tokens"],
        )
        output = (completion.choices[0].message.content or "").strip()

        effective_min_words = _effective_min_words(selected["min_words"], text)

        # Safety net: regenerate once if the model returns an overly short or incomplete answer.
        if _word_count(output) < effective_min_words or _looks_incomplete(output):
            logger.warning(
                "Summary output too short/incomplete for '%s'. Retrying with stronger constraint.",
                normalized_length,
            )
            retry_prompt = (
                f"Your previous answer was too short or incomplete. Regenerate now.\n"
                f"Hard requirements:\n"
                f"- Return a complete, meaningful summary only.\n"
                f"- Minimum words: {effective_min_words}.\n"
                f"- Keep the same target length/style requested earlier ({normalized_length}).\n"
                f"- No sentence fragments and no trailing commas.\n"
            )
            retry_messages = messages + [
                {"role": "assistant", "content": output},
                {"role": "user", "content": retry_prompt},
            ]
            retry_completion = _create_completion_with_fallback(
                client=client,
                messages=retry_messages,
                max_tokens=selected["max_tokens"],
            )
            retry_output = (retry_completion.choices[0].message.content or "").strip()
            if retry_output:
                output = retry_output

        if _has_excessive_verbatim_overlap(text, output):
            logger.warning("Summary appears too extractive. Retrying with explicit paraphrase-only instruction.")
            paraphrase_retry_prompt = (
                "Rewrite the summary using different wording.\n"
                "Hard requirements:\n"
                "- Keep the same meaning and coverage.\n"
                "- Avoid copying source phrasing.\n"
                "- Do not use any 8+ word phrase exactly as it appears in the source.\n"
                "- Keep within the same word budget and format.\n"
            )
            paraphrase_messages = messages + [
                {"role": "assistant", "content": output},
                {"role": "user", "content": paraphrase_retry_prompt},
            ]
            paraphrase_completion = _create_completion_with_fallback(
                client=client,
                messages=paraphrase_messages,
                max_tokens=selected["max_tokens"],
            )
            paraphrase_output = (paraphrase_completion.choices[0].message.content or "").strip()
            if paraphrase_output:
                output = paraphrase_output

        if _is_near_copy(text, output):
            logger.warning("Summary still too similar to source after retries. Using compressive fallback.")
            max_word_map = {"short": 90, "medium": 140, "long": 260}
            output = _extractive_fallback_summary(
                source_text=text,
                min_words=effective_min_words,
                max_words=max_word_map[normalized_length],
                is_bullets=is_bullets,
            )

        if _word_count(output) < effective_min_words or _looks_incomplete(output):
            logger.warning(
                "Model output still too short/incomplete for '%s'. Using deterministic fallback summary.",
                normalized_length,
            )
            max_word_map = {"short": 90, "medium": 140, "long": 260}
            output = _extractive_fallback_summary(
                source_text=text,
                min_words=effective_min_words,
                max_words=max_word_map[normalized_length],
                is_bullets=is_bullets,
            )

        return output
    except Exception as e:
        logger.error(f"Error in Summarizer: {e}")
        raise e