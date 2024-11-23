#
# datapack.py - Код для работы с игровыми пакетами данных.
#


# Импортируем:
import os
import io
import atexit
import zipfile
import tempfile


# Глобальные переменные:
_dp_tmp_files_ = []


# Регистрируем удаление всех временных файлов в случае выхода из программы:
atexit.register(lambda: [(os.remove(f), _dp_tmp_files_.remove(f)) for f in list(_dp_tmp_files_) if os.path.isfile(f)])


# Класс пакета игровых данных:
class DataPackage:
    def __init__(self) -> None:
        self.archive = None

    # Создать пакет данных:
    def create(self, file_path: str, file_folder_list: list | str) -> "DataPackage":
        if isinstance(file_folder_list, str): file_folder_list = [file_folder_list]

        with zipfile.ZipFile(file_path, "w", zipfile.ZIP_DEFLATED) as zipf:
            for item in file_folder_list:
                if os.path.isfile(item): zipf.write(item, os.path.basename(item))
                elif os.path.isdir(item):
                    # Обходим все подкаталоги и файлы:
                    for root, dirs, files in os.walk(item):
                        for file in files:
                            curr_file_path = os.path.join(root, file)
                            # Проверяем, чтобы не добавлять сам архив в себя:
                            if os.path.abspath(curr_file_path) != os.path.abspath(file_path):
                                zipf.write(curr_file_path, os.path.relpath(curr_file_path, os.path.join(item, "..")))
        return self

    # Загружаем архив в память:
    def load(self, path: str) -> "DataPackage":
        with open(path, "rb") as f: self.archive = zipfile.ZipFile(io.BytesIO(f.read()), "r")
        return self

    # Открываем файл в архиве:
    def open(self, path: str) -> io.BytesIO | str:
        global _dp_tmp_files_
        if self.archive is None: raise RuntimeError("Archive is not loaded. Please call \".load()\" first.")
        if path[:2] in ("./", ".\\"): path = path[2:]
        audio_extensions = [".ogg", ".mp3", ".wav", ".flac", ".aac", ".m4a", ".wma", ".aiff", ".alac", ".opus", ".webm"]

        # Если файл имеет одно из аудиорасширений и существует в архиве:
        if os.path.splitext(path)[1].lower() in audio_extensions:
            with self.archive.open(path) as f:
                tf = tempfile.NamedTemporaryFile(delete=False, suffix=os.path.splitext(path)[1]) ; tf.write(f.read())
                tfp = tf.name ; tf.close() ; _dp_tmp_files_.append(tfp) ; return tfp

        # Иначе возвращаем BytesIO файла:
        with self.archive.open(path) as f: return io.BytesIO(f.read())

    # Освобождаем ресурсы:
    def destroy(self) -> None:
        if self.archive: self.archive.close()
        self.archive = None
