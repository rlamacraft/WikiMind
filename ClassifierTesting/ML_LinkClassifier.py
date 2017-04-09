from sklearn import tree
from sklearn.svm import LinearSVC

class LinkClassifier:

    def __init__(self,feature_names,class_names):
        self.feature_names = feature_names
        self.class_names = class_names
        self.classifier = tree.DecisionTreeClassifier()
        # self.classifier = LinearSVC()

    def learn(self,x,y):
        self.classifier.fit(x, y)

    def predict(self,features):
        return(self.classifier.predict([features])[0])

    # only applicable when the classifier is a decision tree
    def createPdf(self,filename):
        from sklearn.externals.six import StringIO
        # import pydot.plus
        dot_data = StringIO()
        tree.export_graphviz(self.classifier,
                                out_file = filename + ".dot",
                                feature_names = self.feature_names,
                                class_names = self.class_names,
                                filled = True, rounded = True, impurity = False)
