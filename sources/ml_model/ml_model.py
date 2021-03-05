from sources.data_processing.queries import ArticleMetadata

class MlModelWrapper:
    def __init__(self, classifier=None):
        self.classifier = classifier

    def predict_article(self, article: ArticleMetadata):
        return False
