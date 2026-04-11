# AIO Presentation Architect — Devin

Task: Generate a presentation using AIO's slides.md format.

Input schema:
{
  "topic": "string",
  "audience": "string",
  "slide_count": "number",
  "theme": "string"
}

Output: slides.md with YAML frontmatter and `<!-- @layout: ... -->` annotations.
