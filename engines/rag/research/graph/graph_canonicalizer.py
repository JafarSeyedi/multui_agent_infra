import re


class GraphCanonicalizer:

    def canonicalize(self, name: str) -> str:

        name = name.lower()
        name = name.strip()

        name = re.sub(r"[-_ ]+", " ", name)

        return name


    def normalize_entity(self, entity):

        entity.name = self.canonicalize(entity.name)

        return entity

