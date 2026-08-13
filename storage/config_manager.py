import json
import os


class ConfigManager:

    def __init__(self, path):
        self.path = path
        self.data = self.load()


    def load(self):

        if not os.path.exists(self.path):
            return {}

        try:
            with open(
                self.path,
                "r",
                encoding="utf-8"
            ) as f:
                return json.load(f)

        except json.JSONDecodeError:
            print("配置文件损坏，重新初始化")
            return {}

        except FileNotFoundError:
            return {}


    def save(self):

        with open(
            self.path,
            "w",
            encoding="utf-8"
        ) as f:

            json.dump(
                self.data,
                f,
                ensure_ascii=False,
                indent=4
            )


    def set(self, key, value):

        self.data[key] = value
        self.save()


    def get(self, key, default=None):

        return self.data.get(
            key,
            default
        )