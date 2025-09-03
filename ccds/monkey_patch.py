# type: ignore
# ruff: noqa

from collections import OrderedDict
from pathlib import Path
from typing import Any, Mapping, MutableMapping, Optional

from cookiecutter.environment import StrictEnvironment
from cookiecutter.exceptions import UndefinedVariableInTemplate
from cookiecutter.generate import generate_context
from cookiecutter.prompt import (
    prompt_choice_for_config,
    read_user_choice,
    read_user_variable,
    render_variable,
)
from jinja2.exceptions import UndefinedError


def apply_user_overrides_to_ccds_context(
    ccds_obj: MutableMapping[str, Any],
    overwrites: Optional[Mapping[str, Any]],
) -> None:
    """Apply user-provided defaults/extras to CCDS context in-place.

    This supports CCDS' extended "choice with subitems" pattern where a choice
    is represented as a list of single-key dictionaries, e.g.::

        dataset_storage = [
            {"none": "none"},
            {"s3": {"bucket": "bucket-name", "aws_profile": "default"}},
            {"gcs": {"bucket": "bucket-name"}},
        ]

    Accepted overwrite shapes for such variables are either::
        {"s3": {"bucket": "my-bucket"}}  # choice + nested fields
        "s3"                                 # just the choice

    For standard list-of-strings choices, both single values and lists
    (multi-choice) are supported. Dicts and scalars are overwritten directly.

    Args:
        ccds_obj: Mutable CCDS context parsed from ``ccds.json``.
        overwrites: Values from Cookiecutter ``default_context`` or ``extra_context``.
            If ``None`` or empty, this is a no-op.
    """
    if not overwrites:
        return

    for key, overwrite in overwrites.items():
        if key not in ccds_obj:
            continue

        context_value = ccds_obj[key]

        if isinstance(context_value, list):
            if not context_value:
                continue

            first_elem = context_value[0]

            # Handle list-of-dicts: choices with subitems
            if isinstance(first_elem, dict):
                if isinstance(overwrite, dict) and len(overwrite) == 1:
                    choice_key = next(iter(overwrite.keys()))
                    sub_overwrite = overwrite[choice_key]
                else:
                    choice_key = overwrite
                    sub_overwrite = None

                # Locate choice and move it to the front
                idx = None
                for i, choice in enumerate(context_value):
                    k = list(choice.keys())[0]
                    if k == choice_key:
                        idx = i
                        break
                if idx is None:
                    continue

                chosen = context_value.pop(idx)
                selected_val = list(chosen.values())[0]

                if isinstance(selected_val, dict) and isinstance(sub_overwrite, dict):
                    selected_val.update(sub_overwrite)
                    chosen = OrderedDict([(choice_key, selected_val)])

                context_value.insert(0, chosen)
                ccds_obj[key] = context_value
                continue

            # Handle standard choice/multichoice (list of strings)
            if isinstance(overwrite, list):
                try:
                    if set(overwrite).issubset(set(context_value)):
                        ccds_obj[key] = overwrite
                except TypeError:
                    # Non-hashable items; ignore
                    pass
                continue

            if overwrite in context_value:
                context_value.remove(overwrite)
                context_value.insert(0, overwrite)
                ccds_obj[key] = context_value
            continue

        if isinstance(context_value, dict) and isinstance(overwrite, dict):
            context_value.update(overwrite)
            ccds_obj[key] = context_value
            continue

        ccds_obj[key] = overwrite


def _prompt_choice_and_subitems(cookiecutter_dict, env, key, options, no_input):
    result = {}

    # first, get the selection
    rendered_options = [
        render_variable(env, list(raw.keys())[0], cookiecutter_dict) for raw in options
    ]

    if no_input:
        selected = rendered_options[0]
    else:
        selected = read_user_choice(key, rendered_options)

    selected_item = [list(c.values())[0] for c in options if list(c.keys())[0] == selected][0]

    result[selected] = {}

    # then, fill in the sub values for that item
    if isinstance(selected_item, dict):
        for subkey, raw in selected_item.items():
            # We are dealing with a regular variable
            val = render_variable(env, raw, cookiecutter_dict)

            if not no_input:
                val = read_user_variable(subkey, val)

            result[selected][subkey] = val
    elif isinstance(selected_item, list):
        val = prompt_choice_for_config(
            cookiecutter_dict,
            env,
            selected,
            selected_item,
            no_input,
        )
        result[selected] = val
    elif isinstance(selected_item, str):
        result[selected] = selected_item

    return result



def prompt_for_config(context, no_input=False):
    """Prompts the user to enter new config, using context as a source for the
    field names and sample values.
    :param no_input: Prompt the user at command line for manual configuration?
    """
    cookiecutter_dict = OrderedDict([])
    env = StrictEnvironment(context=context)

    # First pass: Handle simple and raw variables, plus choices.
    # These must be done first because the dictionaries keys and
    # values might refer to them.
    for key, raw in context["cookiecutter"].items():
        if key.startswith("_"):
            cookiecutter_dict[key] = raw
            continue

        try:
            if isinstance(raw, list):
                if isinstance(raw[0], dict):
                    val = _prompt_choice_and_subitems(
                        cookiecutter_dict,
                        env,
                        key,
                        raw,
                        no_input,
                    )
                    cookiecutter_dict[key] = val
                else:
                    # We are dealing with a choice variable
                    val = prompt_choice_for_config(
                        cookiecutter_dict,
                        env,
                        key,
                        raw,
                        no_input,
                    )
                    cookiecutter_dict[key] = val
            elif not isinstance(raw, dict):
                # We are dealing with a regular variable
                val = render_variable(env, raw, cookiecutter_dict)

                if not no_input:
                    val = read_user_variable(key, val)

                cookiecutter_dict[key] = val
        except UndefinedError as err:
            msg = f"Unable to render variable '{key}'"
            raise UndefinedVariableInTemplate(msg, err, context)

    # Second pass; handle the dictionaries.
    for key, raw in context["cookiecutter"].items():
        try:
            if isinstance(raw, dict):
                # We are dealing with a dict variable
                val = render_variable(env, raw, cookiecutter_dict)

                if not no_input:
                    val = read_user_dict(  # noqa: F821 referencable in patched context
                        key,
                        val,
                    )

                cookiecutter_dict[key] = val
        except UndefinedError as err:
            msg = f"Unable to render variable '{key}'"
            raise UndefinedVariableInTemplate(msg, err, context)

    return cookiecutter_dict


def generate_context_wrapper(*args, **kwargs):
    """Hardcoded in cookiecutter, so we override:
    https://github.com/cookiecutter/cookiecutter/blob/2bd62c67ec3e52b8e537d5346fd96ebd82803efe/cookiecutter/main.py#L85
    """
    # replace full path to cookiecutter.json with full path to ccds.json
    kwargs["context_file"] = str(Path(kwargs["context_file"]).with_name("ccds.json"))

    # Cookiecutter's apply_overwrites_to_context doesn't understand our
    # list-of-dicts "choice with subitems" structure (e.g., dataset_storage).
    # To avoid warnings/errors, we apply defaults/extra ourselves after loading.
    user_defaults = kwargs.pop("default_context", None)
    user_extras = kwargs.pop("extra_context", None)

    parsed_context = generate_context(*args, **kwargs)

    # Apply defaults/extras with support for subchoice structures
    ccds_obj = parsed_context.get("ccds")
    if isinstance(ccds_obj, dict):
        apply_user_overrides_to_ccds_context(ccds_obj, user_defaults)
        apply_user_overrides_to_ccds_context(ccds_obj, user_extras)

    # replace key
    parsed_context["cookiecutter"] = parsed_context["ccds"]
    del parsed_context["ccds"]
    return parsed_context
