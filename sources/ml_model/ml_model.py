from typing import Tuple

from sources.data_processing.queries import ArticleMetadata
from sources.ml_model.pytorch_model import PytorchModel


class MlModelWrapper:
    """The interface that needs to be implemented by the MLModel.

    CURRENTLY having problems with integration! So dummy classifier is used.
    """

    def __init__(self, classifier=None):
        self.classifier = PytorchModel()

    def predict_article(self, article: ArticleMetadata) -> Tuple[bool, float]:
        """Predicts the relevance of an article based on its abstract.

        Args:
            article (ArticleMetadata): The article to be judged.

        Returns:
            bool: True if relevant, False otherwise.
        """
        # return False
        return self.classifier.b(article.title, article.journal_name, article.abstract)
