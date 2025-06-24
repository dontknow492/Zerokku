from enum import Enum

from utils.scripts import resource_path

class AssetPlaceholder(Enum):
    IMAGE = 'image.jpg'
    PERSON = 'person.png'

    def path(self):
        return resource_path(f"assets\\placeholders\\{self.value}")



if __name__ == '__main__':
    print(AssetPlaceholder.IMAGE.path())