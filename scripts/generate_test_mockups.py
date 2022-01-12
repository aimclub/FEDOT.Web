from app.singletons.db_service import DBServiceSingleton
from init.init_cases import create_default_cases
from init.init_history import create_default_history
from init.init_pipelines import create_default_pipelines

if __name__ == "__main__":
    DBServiceSingleton()
    create_default_cases()
    create_default_pipelines()
    create_default_history(opt_times=None)
