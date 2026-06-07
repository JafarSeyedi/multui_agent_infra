import os
import re
import yaml
from typing import List, Optional, Dict, Any
from .models import Skill


class SkillLoader:
    def __init__(self, skills_directory: str):
        """
        Initialize the skill loader with a root directory to search for skills.
        """
        self.skills_directory = skills_directory
        self._skills_data: Dict[str, Dict[str, Any]] = {}  # identifier -> {skill: Skill, base_path: str}
        self._load_all_skills()

    def _load_all_skills(self):
        """
        Recursively scan the skills_directory for SKILL.md files and load them.
        """
        for root, dirs, files in os.walk(self.skills_directory):
            for file in files:
                if file == "SKILL.md":
                    skill_path = os.path.join(root, file)
                    skill = self._load_skill_from_file(skill_path)
                    if skill:
                        # Use the relative path from the skills_directory as the identifier
                        relative_path = os.path.relpath(skill_path, self.skills_directory)
                        skill_dir = os.path.dirname(skill_path)
                        self._skills_data[relative_path] = {
                            'skill': skill,
                            'base_path': skill_dir
                        }

    def _load_skill_from_file(self, file_path: str) -> Optional[Skill]:
        """
        Load a single skill from a SKILL.md file.
        The file is expected to have a YAML frontmatter between --- lines.
        """
        try:
            with open(file_path, 'r') as f:
                content = f.read()
        except Exception as e:
            print(f"Error reading skill file {file_path}: {e}")
            return None

        # Split the content by the frontmatter delimiter
        parts = re.split(r'^---\s*$', content, flags=re.MULTILINE, maxsplit=2)
        if len(parts) < 3:
            # No frontmatter found, treat the entire file as content with default metadata?
            # But we require at least a name and description, so we'll return None.
            print(f"Skill file {file_path} does not have a valid YAML frontmatter.")
            return None

        # parts[0] is empty if the file starts with ---
        # parts[1] is the YAML frontmatter
        # parts[2] is the rest of the content (the skill body)
        frontmatter = parts[1]
        skill_body = parts[2].strip()

        try:
            metadata = yaml.safe_load(frontmatter)
        except yaml.YAMLError as e:
            print(f"Error parsing YAML frontmatter in {file_path}: {e}")
            return None

        # Extract references from the skill body? We'll assume references are listed in the frontmatter.
        # But the Agent Skills standard might have references in the body. We'll stick to frontmatter for now.
        # However, we can also look for reference links in the body and extract them? 
        # For simplicity, we'll only use the references from the frontmatter.

        # Create the Skill object
        try:
            skill = Skill(
                name=metadata.get('name', ''),
                description=metadata.get('description', ''),
                version=metadata.get('version', '1.0.0'),
                author=metadata.get('author'),
                tags=metadata.get('tags', []),
                inputs=metadata.get('inputs', []),
                outputs=metadata.get('outputs', []),
                references=metadata.get('references', []),
                content=skill_body,
                steps=metadata.get('steps', None)
            )
        except Exception as e:
            print(f"Error creating Skill object from {file_path}: {e}")
            return None

        return skill

    def get_skill(self, skill_identifier: str) -> Optional[Skill]:
        """
        Get a skill by its identifier (relative path from the skills directory).
        """
        data = self._skills_data.get(skill_identifier)
        if data:
            return data['skill']
        return None

    def get_skill_base_path(self, skill_identifier: str) -> Optional[str]:
        """
        Get the base directory (directory containing the SKILL.md file) for a skill.
        """
        data = self._skills_data.get(skill_identifier)
        if data:
            return data['base_path']
        return None

    def list_skills(self) -> List[str]:
        """
        List all skill identifiers (relative paths) that have been loaded.
        """
        return list(self._skills_data.keys())

    def get_skill_by_name(self, name: str) -> Optional[Skill]:
        """
        Get a skill by its name (first match). Note: if there are multiple skills with the same name, 
        this returns the first one found.
        """
        for data in self._skills_data.values():
            if data['skill'].name == name:
                return data['skill']
        return None