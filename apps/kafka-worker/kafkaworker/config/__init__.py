from pconf import Pconf
import os

dir_path = os.path.dirname(os.path.realpath(__file__))

Pconf.env(separator="__")
Pconf.file(f"{dir_path}/default.yaml", encoding="yaml")
config = Pconf.get()
