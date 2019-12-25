import numpy as np
np.set_printoptions(suppress=True, precision=4)
import matplotlib.pyplot as plt
from sklearn.model_selection import train_test_split
import tensorflow as tf
from tensorflow import keras

from img_processing import *
from blob_series_tracker import *
from neural_network import *

def classification_demo(X, y):
    X = np.array(X)
    y = np.array(y)

    X_train, X_test, y_train, y_test = train_test_split(X, y, stratify=y, 
                                                        test_size=0.33,
                                                        random_state=1)

    model = default_grain_classifier_model()

    model.compile(optimizer='adam',
                  loss='sparse_categorical_crossentropy',
                  metrics=['accuracy'])
    
    history = model.fit(X_train, y_train, epochs=300, verbose=0)

    print("Test y:", y_test)
    print("Test y:", [decode_labels(y) for y in y_test])
    print('Test prediction scores:\n', model.predict(X_test))
    prediction = model.predict_classes(X_test)
    print('Test prediction classification:\n', prediction)
    print('Test prediction classification:\n',
          [decode_labels(y) for y in prediction])
    print('Model evaluation loss and accuracy:\n', 
          model.evaluate(X_test, y_test, verbose=0),
          '\n')

    fig = plt.figure()
    ax = plt.subplot(111)
    plt.plot(history.history['accuracy'], c='b', label='mar')
    plt.title('Model training history')
    plt.ylabel('Accuracy')
    plt.xlabel('Epoch')
    
    plt.twinx()
    plt.plot(history.history['loss'], c='r', label='cepan')
    plt.title('Model training history')
    plt.ylabel('Loss')
    plt.xlabel('Epoch')
    
    ax.legend(loc=0)

if __name__ == '__main__':
    X, y = default_img_set()
    X = [[full_prepare(img) for img in same_sample] for same_sample in X]

    Xs = count_blobs_with_all_methods(X)
    
    demo_names = ['All blobs detection',
                  'Detect only remaining blobs',
                  'Percentage of remaining blobs']
    for X, demo_name in zip(Xs, demo_names):
        print(demo_name)
        classification_demo(X, y)

    plt.show()
