import logging

logger = logging.getLogger(__name__)


class SemanticVersion:

    def __init__(self, semantic_version):
        self.__start_semantic_version = semantic_version
        self.__semantic_version = semantic_version
        self.__bumps = [] 
    
    def bump(self, version_bump):
        logger.debug(f"Performing {version_bump.name.lower()} bump")
        version_numbers = self.__semantic_version.split(".")

        for index, value in enumerate(version_numbers[version_bump.value:]):
            version_index = version_bump.value + index
            if not index:
                # Bump the value of the given version category
                version_numbers[version_index] = str(int(value) + 1)
                continue
            # Reset any version categories that follow to zero
            version_numbers[version_index] = "0"

        self.__semantic_version = ".".join(version_numbers)
        self.__bumps.append(version_bump)
        logger.debug(f"Bumped semantic version to {self.__semantic_version}")
        return self.__semantic_version

        
    def has_changed(self):
        return self.__start_semantic_version != self.__semantic_version
    
    def start_value(self):
        return self.__start_semantic_version
    
    def __str__(self):
        return self.__semantic_version