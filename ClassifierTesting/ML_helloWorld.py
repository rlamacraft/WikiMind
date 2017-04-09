from sklearn import tree

# these are weights and whether the fruit is bumpy (0) or smooth (1)
features = [[150, 0], [170, 0], [140, 1], [130, 1]]
# these are fruits: apples (0) or oranges (1)
labels = [1, 1, 0, 0]

clf = tree.DecisionTreeClassifier()
clf = clf.fit(features, labels)
print(clf.predict([[160,0]]))
