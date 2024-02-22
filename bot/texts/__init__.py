import os


class TextService:
    @classmethod
    def get_text(cls, section: str, slug: str) -> str:
        file_path = f'bot/texts/{section}/{slug}.md'
        if os.path.exists(file_path):
            with open(file_path, 'r') as text:
                return text.read()
        return ''
