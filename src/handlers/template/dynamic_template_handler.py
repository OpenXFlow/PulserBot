# The MIT License (MIT)
# Copyright (c) 2025 Jozef Darida  (LinkedIn/Xing)
# For full license text, see the LICENSE file in the project root.

# src/handlers/template/dynamic_template_handler.py
"""
Handler for the 'dynamic_template' theme type with an optimized OOP design.
"""

import logging
from abc import ABC, abstractmethod
from dataclasses import asdict
from pathlib import Path
from typing import Any, Dict, List, Optional, Tuple, Union, cast

from ...services import sheets_service
from .._base.base_handler import BaseHandler
from .dynamic_template_models import GermanLessonModelRegistry, GermanTerm, GermanVerb

# ============================================================================
# Processing Context
# ============================================================================


class ProcessingContext:
    """A state container that holds all data during the pipeline's execution."""

    def __init__(self, theme_config: Dict[str, Any], lang: str) -> None:
        """
        Initializes the context with the initial theme and language configuration.

        Args:
            theme_config (Dict[str, Any]): The configuration for the specific theme.
            lang (str): The language key for the content.
        """
        self.theme_config: Dict[str, Any] = theme_config
        self.lang: str = lang
        self.theme_name: str = theme_config.get("theme_name", "Unknown Theme")
        self.rotation_ws: Optional[Any] = None
        self.rotation_idx: Optional[int] = None
        self.content_key: Optional[str] = None
        self.template_path: Optional[str] = None
        self.lesson_ws: Optional[Any] = None
        self.lesson_idx: Optional[int] = None
        self.lesson_data: Optional[Dict[str, Any]] = None
        self.data_model: Optional[Union[GermanTerm, GermanVerb]] = None
        self.final_text: Optional[str] = None
        self.image_url: Optional[str] = None


# ============================================================================
# Processing Steps (Strategy Pattern)
# ============================================================================


class ProcessingStep(ABC):
    """An abstract base class for a single step in the processing pipeline."""

    @abstractmethod
    def execute(self, context: ProcessingContext) -> bool:
        """
        Executes the logic for this step.

        Args:
            context (ProcessingContext): The shared context object for the pipeline.

        Returns:
            bool: True if the step was successful, False to halt the pipeline.
        """
        pass


class RotationKeyFetcher(ProcessingStep):
    """Fetches the content key from the rotation worksheet."""

    def execute(self, context: ProcessingContext) -> bool:
        """
        Finds an unused row in the rotation sheet and extracts the content key.

        Args:
            context (ProcessingContext): The shared context to populate.

        Returns:
            bool: True on success, False on failure.
        """
        rotation_ref = context.theme_config.get("content_rotation_source")
        if not rotation_ref:
            logging.error("Missing 'content_rotation_source' in theme config.")
            return False
        context.rotation_ws = sheets_service.get_worksheet(rotation_ref)
        if not context.rotation_ws:
            return False
        idx, data = sheets_service.get_unused_item(context.rotation_ws, language=None)
        if not data or idx is None or not (key := data.get("content")):
            logging.error("Could not get a valid content key from rotation sheet.")
            return False
        context.rotation_idx, context.content_key = idx, str(key).strip()
        return True


class TemplateSelector(ProcessingStep):
    """Selects the appropriate template path based on the content key."""

    def execute(self, context: ProcessingContext) -> bool:
        """
        Determines if a 'verb' or 'other' template should be used.

        Args:
            context (ProcessingContext): The shared context to populate.

        Returns:
            bool: True on success, False if the path cannot be determined.
        """
        try:
            prompt_config = context.theme_config["prompts"][context.lang]
            normalized_key = GermanLessonModelRegistry._normalize_key(
                context.content_key or ""
            )

            if normalized_key in ["verbs_irregular", "verbs_regular"]:
                context.template_path = cast(str, prompt_config.get("verbs"))
            else:
                context.template_path = cast(str, prompt_config.get("other"))

            if not context.template_path:
                raise KeyError("Template path for this content category not found.")
            return True
        except KeyError as e:
            logging.error(f"Could not determine template path: {e}")
            return False


class LessonDataFetcher(ProcessingStep):
    """Fetches the main lesson data from the corresponding worksheet."""

    def execute(self, context: ProcessingContext) -> bool:
        """
        Uses the content key to open the correct lesson sheet and fetch an unused row.

        Args:
            context (ProcessingContext): The shared context to populate.

        Returns:
            bool: True on success, False on failure.
        """
        rotation_ref = context.theme_config.get("content_rotation_source", {})
        lesson_ref = {
            "spreadsheet_key": rotation_ref.get("spreadsheet_key"),
            "worksheet_key": context.content_key,
        }
        context.lesson_ws = sheets_service.get_worksheet(lesson_ref)
        if not context.lesson_ws:
            return False
        idx, data = sheets_service.get_unused_item(context.lesson_ws, None)
        if not data or idx is None:
            logging.warning(
                f"No unused content in sheet for key '{context.content_key}'."
            )
            return False
        context.lesson_idx, context.lesson_data = idx, data
        return True


class DataModelBuilder(ProcessingStep):
    """Builds the structured data model for the lesson."""

    def execute(self, context: ProcessingContext) -> bool:
        """
        Uses the registry to get the correct dataclass and instantiates it.

        Args:
            context (ProcessingContext): The shared context to populate.

        Returns:
            bool: True on success, False on failure.
        """
        model_class = GermanLessonModelRegistry.get_model_class_for_key(
            context.content_key or ""
        )
        if not context.lesson_data:
            return False
        try:
            context.data_model = model_class.from_dict(context.lesson_data)
            return True
        except Exception as e:
            logging.error(
                f"Failed to build data model for '{context.content_key}': {e}"
            )
            return False


class TextFormatter(ProcessingStep):
    """Builds all placeholders and formats the final text."""

    def _get_auxiliary_links(self) -> Dict[str, str]:
        """
        Fetches auxiliary 'Slow German' and grammar links.

        Returns:
            Dict[str, str]: A dictionary with the HTML for the links.
        """
        links = {
            "dynamic_link_html": "",
            "static_grammar_link_html": 'Preskúmajte gramatiku na:\n<a href="https://deutsch.info/grammar">Deutsch.info</a>',
        }
        sg_ref = {
            "spreadsheet_key": "YDP_LLM_Dynamic_GermanLesson",
            "worksheet_key": "slow_german_links",
        }
        sg_ws = sheets_service.get_worksheet(sg_ref)
        if sg_ws:
            idx, data = sheets_service.get_unused_item(sg_ws, None)
            if data and idx:
                title, link = (
                    str(data.get("name", "")).strip(),
                    str(data.get("link", "")).strip(),
                )
                links["dynamic_link_html"] = (
                    f'Dnešná audio lekcia nemčiny:\n<a href="{link}">{title}</a>'
                )
                sheets_service.mark_item_as_used(sg_ws, idx)
        return links

    def _get_footer_content(self) -> str:
        """
        Gets the AI links footer content from its template file.

        Returns:
            str: The content of the footer file.
        """
        try:
            return (
                Path("src/resources/template/footer_ai_links_slovak.txt")
                .read_text(encoding="utf-8")
                .strip()
            )
        except FileNotFoundError:
            logging.warning("AI links footer file not found.")
            return ""

    def execute(self, context: ProcessingContext) -> bool:
        """
        Builds the complete placeholder dictionary and formats the final text.

        Args:
            context (ProcessingContext): The shared context to read from and populate.

        Returns:
            bool: True on success, False on failure.
        """
        if not context.data_model or not context.template_path:
            return False
        try:
            template_str = Path(context.template_path).read_text(encoding="utf-8")
        except FileNotFoundError:
            logging.error(f"Template file not found: {context.template_path}")
            return False

        placeholders = asdict(context.data_model)
        placeholders["lesson_title"] = GermanLessonModelRegistry.create_title_from_key(
            context.content_key or ""
        )
        placeholders.update(self._get_auxiliary_links())
        placeholders["AI_LINKS_FOOTER"] = self._get_footer_content()
        placeholders["IMAGE_ATTRIBUTION"] = ""

        if isinstance(context.data_model, GermanTerm):
            placeholders["term_plural_line"] = (
                f"({context.data_model.term_plural})"
                if context.data_model.term_plural
                else ""
            )
            for i in range(1, 9):
                sent = (
                    context.data_model.sentences[i - 1]
                    if i <= len(context.data_model.sentences)
                    else {}
                )
                placeholders[f"sentence{i}_de"], placeholders[f"sentence{i}_en"] = (
                    sent.get("de", ""),
                    sent.get("en", ""),
                )

        if isinstance(context.data_model, GermanVerb):
            tenses = [
                "present",
                "preterite",
                "perfect",
                "plusquamperfekt",
                "futur1",
                "futur2",
            ]
            for i, tense in enumerate(tenses):
                sent = (
                    context.data_model.sentences[i]
                    if i < len(context.data_model.sentences)
                    else {}
                )
                (
                    placeholders[f"sentence_{tense}_de"],
                    placeholders[f"sentence_{tense}_en"],
                ) = sent.get("de", ""), sent.get("en", "")

        try:
            context.final_text = template_str.format_map(placeholders)
        except KeyError as e:
            logging.error(
                f"Required placeholder {e} missing in template for '{context.theme_name}'."
            )
            return False

        norm_key = GermanLessonModelRegistry._normalize_key(context.content_key or "")
        img_key = f"static_image_{norm_key}_url"
        context.image_url = context.theme_config.get(
            img_key
        ) or context.theme_config.get("static_image_url")
        return True


class ItemMarker(ProcessingStep):
    """A final pipeline step to mark all used Google Sheet rows."""

    def execute(self, context: ProcessingContext) -> bool:
        """
        Marks the row in the rotation sheet and the main lesson sheet as used.

        Args:
            context (ProcessingContext): The shared context.

        Returns:
            bool: Always True, as errors here should not halt the pipeline.
        """
        if context.rotation_ws and context.rotation_idx:
            sheets_service.mark_item_as_used(context.rotation_ws, context.rotation_idx)
        if context.lesson_ws and context.lesson_idx:
            sheets_service.mark_item_as_used(context.lesson_ws, context.lesson_idx)
        return True


# ============================================================================
# Main Handler and Pipeline
# ============================================================================


class ProcessingPipeline:
    """Executes a sequence of processing steps."""

    def __init__(self, steps: List[ProcessingStep]):
        """
        Initializes the pipeline with a list of steps.

        Args:
            steps (List[ProcessingStep]): The sequence of steps to execute.
        """
        self.steps = steps

    def run(self, context: ProcessingContext) -> bool:
        """
        Executes each step, halting on the first failure.

        Args:
            context (ProcessingContext): The shared context object.

        Returns:
            bool: True if all steps succeeded, False otherwise.
        """
        for step in self.steps:
            if not step.execute(context):
                return False
        return True


class DynamicTemplateHandler(BaseHandler):
    """
    Handles complex themes that use dynamic template selection without an LLM.
    """

    def __init__(self, theme_config: Dict[str, Any], lang: str) -> None:
        """
        Initializes the handler and its processing pipeline.

        Args:
            theme_config (Dict[str, Any]): The configuration for the specific theme.
            lang (str): The language key for the content.
        """
        super().__init__(theme_config, lang)
        self._pipeline = self._build_pipeline()

    def _build_pipeline(self) -> ProcessingPipeline:
        """
        Constructs the sequence of processing steps for this handler.

        Returns:
            ProcessingPipeline: An instance of the pipeline with all required steps.
        """
        return ProcessingPipeline(
            [
                RotationKeyFetcher(),
                TemplateSelector(),
                LessonDataFetcher(),
                DataModelBuilder(),
                TextFormatter(),
                ItemMarker(),
            ]
        )

    def _process(self, **kwargs: Any) -> Tuple[Optional[str], Optional[str]]:
        """
        Orchestrates content generation by running the processing pipeline.

        Args:
            **kwargs: Additional keyword arguments (ignored).

        Returns:
            Tuple[Optional[str], Optional[str]]: A tuple (text, image_url), or (None, None).
        """
        context = ProcessingContext(self.theme_config, self.lang)
        if self._pipeline.run(context):
            return context.final_text, context.image_url
        return None, None


# End of src/handlers/template/dynamic_template_handler.py (v. 0043)
