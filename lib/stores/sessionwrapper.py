from sqlalchemy.orm import Session


class SessionWrapper:

    def __init__(self, inner_session: Session):
        self.session = inner_session

    def __enter__(self):
        return self.session

    def __exit__(self, exc_type, exc_val, exc_tb):
        self.session.close()
