'''Generate images, plots and tables for bachelor's thesis paper.'''

import csv
import os

import matplotlib.pyplot as plt
import numpy as np
from skimage.color import rgb2gray
from skimage.filters import threshold_otsu
from skimage.io import imread, imsave
from skimage.transform import rescale
from skimage.util import invert, img_as_ubyte
import tikzplotlib
from sklearn.model_selection import train_test_split
from tensorflow import keras

from blob_analysis import (count_blobs_with_all_methods, patch_plot_legend,
                           plot_blob_stat)
from blob_detection_compare_demo import compare_detection
from blob_series_tracker import (find_blob_series,
                                 ratio_of_remaining_blobs_in_stages)
from img_processing import (crop_ui, default_img_set, full_prepare,
                            load_img_series)
from neural_network import (default_grain_classifier_model,
                            network_cross_validation, mean_confusion_matrix)


def temp_bounds_imgs_gen():
    img = imread('img/103_E5R_1.jpg')
    img = rgb2gray(img)
    img = invert(img)

    bounds = (((6, 24), (283, 318)),
              ((219, 236), (283, 318)))

    for bound in bounds:
        bound_img = img[slice(*bound[0]), slice(*bound[1])]
        bound_img = rescale(bound_img, 4, anti_aliasing=True)
        thr = threshold_otsu(bound_img)
        img_txt = bound_img > thr

        plt.figure()
        plt.imshow(bound_img, cmap="gray")
        plt.axis('off')
        imsave('exports/temp_bounds_scale.png', img_as_ubyte(bound_img))
        plt.figure()
        plt.axis('off')
        plt.imshow(img_txt, cmap="gray")
        imsave('exports/temp_bounds_bin.png', img_as_ubyte(img_txt))


def grain_samples_imgs_gen():
    samples_names = ('104_E5R', '117_E6R')
    for name in samples_names:
        imgs = load_img_series('img/' + name)
        for i, img in enumerate(imgs):
            img = rgb2gray(img)
            imsave('exports/' + name + '_' + str(i) + '.png',
                   img_as_ubyte(crop_ui(img)))


def blob_detection_compare_plots_gen():
    img = imread('img/104_E5R_0.jpg')
    img_crop = crop_ui(rgb2gray(img))
    img_prep = full_prepare(img)
    blobs_list = compare_detection(img_prep)

    suffixes = ('LoG', 'DoG', 'DoH')

    for blobs, suffix in zip(blobs_list, suffixes):
        _, ax = plt.subplots()
        plt.title('Liczba wykrytych detali: {}'.format(len(blobs)))
        plt.imshow(img_crop, cmap=plt.get_cmap('gray'))
        for blob in blobs:
            y, x, r = blob
            c = plt.Circle((x, y), r, color='r', fill=False)
            ax.add_patch(c)

        ax.set_axis_off()
        tikzplotlib.save('exports/blob_detection_compare_' + suffix)


def blob_count_plots_gen():
    imgs = load_img_series('img/104_E5R')
    imgs_prep = [full_prepare(img) for img in imgs]
    imgs_crop = [crop_ui(rgb2gray(img)) for img in imgs]

    stages_all = find_blob_series(imgs_prep, only_remaining=False)
    stages_rem = find_blob_series(imgs_prep)

    # Map stages on first image
    colors = ('blue', 'blueviolet', 'magenta', 'crimson', 'red')
    fig = plt.figure(frameon=False)
    ax = fig.add_axes([0, 0, 1, 1])
    plt.imshow(imgs_crop[0], cmap=plt.get_cmap('gray'))
    for stage, color in zip(stages_rem, colors):
        for blob in stage:
            y, x, r = blob
            c = plt.Circle((x, y), r, color=color, fill=False)
            ax.add_patch(c)
    ax.set_axis_off()
    plt.savefig('exports/blob_tracker', dpi=300)

    # Show two methods combined to compare
    loop_set = enumerate(zip(stages_rem, stages_all, imgs_crop))
    for i, (stage_rem, stage_all, img) in loop_set:
        fig = plt.figure(frameon=False)
        ax = fig.add_axes([0, 0, 1, 1])
        plt.imshow(img, cmap=plt.get_cmap('gray'))
        for blob_all in stage_all:
            y, x, r = blob_all
            c = plt.Circle((x, y), r, color='b', fill=False)
            ax.add_patch(c)
        for blob_rem in stage_rem:
            y, x, r = blob_rem
            c = plt.Circle((x, y), r, color='r', fill=False)
            ax.add_patch(c)

        ax.set_axis_off()
        plt.savefig('exports/blob_tracker_min_' + str(i))


def blob_ratio_table_gen():
    sample_names = ('104_E5R', '106_E11R', '107_E6R', '111_E16R')

    with open('exports/neural_network_comparison.csv', 'w') as csvfile:
        filewriter = csv.writer(csvfile, delimiter=';')
        # Header
        filewriter.writerow(('Próbka', 'Minuta 0', 'Minuta 1', 'Minuta 2',
                             'Minuta 3', 'Minuta 4'))
        for name in sample_names:
            imgs = load_img_series('img/' + name)
            imgs_prep = [full_prepare(img) for img in imgs]
            stages_rem = find_blob_series(imgs_prep)
            ratios = ratio_of_remaining_blobs_in_stages(stages_rem)
            ratios = (round(ratio, 2) for ratio in ratios)
            filewriter.writerow((name, *ratios))


def blob_analysis_plots_gen():
    X, y = default_img_set()
    X = [[full_prepare(img) for img in same_sample] for same_sample in X]

    Xa, Xr, Xp = count_blobs_with_all_methods(X)

    colors = ('r', 'g', 'b', 'y')
    labels = ('E5R', 'E11R', 'E6R', 'E16R')

    plot_blob_stat(Xa, y, colors)
    plt.title('Liczba wszystkich detali')
    plt.xlabel('Minuty')
    plt.ylabel('Liczba detali')
    patch_plot_legend(colors, labels)
    tikzplotlib.save('exports/blob_analysis_all')

    plot_blob_stat(Xr, y, colors)
    plt.title('Liczba śledzonych detali')
    plt.xlabel('Minuty')
    plt.ylabel('Liczba detali')
    patch_plot_legend(colors, labels)
    tikzplotlib.save('exports/blob_analysis_remaining')

    plot_blob_stat(Xp, y, colors)
    plt.title('Pozostały procent śledzonych detali')
    plt.xlabel('Minuty')
    plt.ylabel('Liczba detali')
    patch_plot_legend(colors, labels)
    tikzplotlib.save('exports/blob_analysis_ratio')


def neural_network_trainig_plots_gen():
    X, y = default_img_set()
    X = [[full_prepare(img) for img in same_sample] for same_sample in X]
    Xs = count_blobs_with_all_methods(X)

    files_suffixes = ('all', 'remaining', 'ratio')

    for X, suffix in zip(Xs, files_suffixes):
        X = np.array(X)
        y = np.array(y)

        X_train, _, y_train, _ = train_test_split(
            X, y, stratify=y, test_size=0.33, random_state=1)

        model = default_grain_classifier_model()
        model.compile(
            optimizer='adam',
            loss='sparse_categorical_crossentropy',
            metrics=['accuracy'])
        history = model.fit(X_train, y_train, epochs=300, verbose=0)

        plt.figure()
        plt.title('Historia treningu modelu')
        plt.xlabel('Epoka')

        plt.plot(history.history['accuracy'], c='b')
        plt.plot(history.history['loss'], c='r')

        plt.legend(('Dokładność', 'Błąd'))

        tikzplotlib.save('exports/neural_network_trainig_' + suffix)


def neural_network_test_table_gen():
    X, y = default_img_set()
    X = [[full_prepare(img) for img in same_sample] for same_sample in X]
    Xs = count_blobs_with_all_methods(X)
    Xs = [np.array(X_count) for X_count in Xs]
    y = np.array(y)

    row_names = ('Wszystkie detale', 'Śledzone detale',
                 'Stosunek śledzonych detali')

    with open('exports/neural_network_test.csv', 'w') as csvfile:
        filewriter = csv.writer(csvfile, delimiter=';')
        # Header
        filewriter.writerow(('Metoda zliczania detali', 'Wskaźnik', 
                             'wskaźnik'))
        filewriter.writerow(('Metoda zliczania detali', 'Błąd', 'Dokładność'))

        for X, name in zip(Xs, row_names):
            X = np.array(X)
            X_train, X_test, y_train, y_test = train_test_split(
                X, y, stratify=y, test_size=0.33, random_state=1)

            model = default_grain_classifier_model()
            model.compile(
                optimizer='adam',
                loss='sparse_categorical_crossentropy',
                metrics=['accuracy'])
            model.fit(X_train, y_train, epochs=300, verbose=0)

            score = model.evaluate(X_test, y_test, verbose=0)
            filewriter.writerow((name, *score))


def neural_network_validation_table_gen():
    X, y = default_img_set()
    X = [[full_prepare(img) for img in same_sample] for same_sample in X]
    Xs = count_blobs_with_all_methods(X)
    Xs = [np.array(X_count) for X_count in Xs]
    y = np.array(y)

    row_names = ('Wszystkie detale', 'Śledzone detale',
                 'Stosunek śledzonych detali')

    with open('exports/neural_network_validation.csv', 'w') as csvfile:
        filewriter = csv.writer(csvfile, delimiter=';')
        # Header
        filewriter.writerow(('Metoda zliczania detali', 'Wskaźnik', 
                     'wskaźnik'))
        filewriter.writerow(('Metoda zliczania detali', 'Błąd', 'Dokładność'))

        for X, name in zip(Xs, row_names):
            model = default_grain_classifier_model()
            model.compile(
                optimizer='adam',
                loss='sparse_categorical_crossentropy',
                metrics=['accuracy'])

            scores = np.array(network_cross_validation(model, X, y, 3))
            score = np.round(scores.mean(axis=0), 2)
            filewriter.writerow((name, *score))


def network_comparison_table_gen():
    X, y = default_img_set()
    X = [[full_prepare(img) for img in same_sample] for same_sample in X]
    X = [
        ratio_of_remaining_blobs_in_stages(find_blob_series(img_series))
        for img_series in X
    ]
    X = np.array(X)
    y = np.array(y)

    with open('exports/neural_network_comparison.csv', 'w') as csvfile:
        filewriter = csv.writer(csvfile, delimiter=';')
        # Header
        filewriter.writerow(('Parametr', 'Wartość', 'Błąd', 'Dokładność'))

        # Activation functions
        activation_funcs = ('sigmoid', 'relu', 'elu', 'tanh')
        for func in activation_funcs:
            model = keras.Sequential([
                keras.layers.Dense(5, activation=func),
                keras.layers.Dense(256, activation=func),
                keras.layers.Dense(128, activation=func),
                keras.layers.Dense(4, activation='softmax')
            ])

            model.compile(
                optimizer='adam',
                loss='sparse_categorical_crossentropy',
                metrics=['accuracy'])
            scores = np.array(network_cross_validation(model, X, y, 3))
            score = np.round(scores.mean(axis=0), 2)

            filewriter.writerow(('Funkcja aktywacji', func, *score))

        # Number of hidden layers
        models = []
        models.append(
            keras.Sequential([
                keras.layers.Dense(5, activation='tanh'),
                keras.layers.Dense(512, activation='tanh'),
                keras.layers.Dense(4, activation='softmax')
            ]))
        models.append(
            keras.Sequential([
                keras.layers.Dense(5, activation='tanh'),
                keras.layers.Dense(256, activation='tanh'),
                keras.layers.Dense(128, activation='tanh'),
                keras.layers.Dense(4, activation='softmax')
            ]))

        for model, i in zip(models, (1, 2)):
            model.compile(
                optimizer='adam',
                loss='sparse_categorical_crossentropy',
                metrics=['accuracy'])
            scores = np.array(network_cross_validation(model, X, y, 3))
            score = np.round(scores.mean(axis=0), 2)

            filewriter.writerow(('Liczba warstw ukrytych', i, *score))

        # Number of neurons in hidden layers
        neurons_num = ((128, 64), (256, 128), (512, 126))

        for num in neurons_num:
            model = keras.Sequential([
                keras.layers.Dense(5, activation='tanh'),
                keras.layers.Dense(num[0], activation='tanh'),
                keras.layers.Dense(num[1], activation='tanh'),
                keras.layers.Dense(4, activation='softmax')
            ])

            model.compile(
                optimizer='adam',
                loss='sparse_categorical_crossentropy',
                metrics=['accuracy'])
            scores = np.array(network_cross_validation(model, X, y, 3))
            score = np.round(scores.mean(axis=0), 2)

            filewriter.writerow(('Liczba neuronów w warstwach ukrytych',
                                 '{} i {}'.format(num[0], num[1]), *score))

        # Optimizer
        model = default_grain_classifier_model()
        optimizers = ('sgd', 'adam')
        for opt in optimizers:
            model.compile(
                optimizer=opt,
                loss='sparse_categorical_crossentropy',
                metrics=['accuracy'])
            scores = np.array(network_cross_validation(model, X, y, 3))
            score = np.round(scores.mean(axis=0), 2)

            filewriter.writerow(('Algorytm uczenia', opt, *score))


def confusion_matrix_table_gen():
    X, y = default_img_set()
    X = [[full_prepare(img) for img in same_sample] for same_sample in X]
    X = count_blobs_with_all_methods(X)[2]
    X = np.array(X)
    y = np.array(y)

    model = default_grain_classifier_model()
    model.compile(
        optimizer='adam',
        loss='sparse_categorical_crossentropy',
        metrics=['accuracy'])

    mcm = mean_confusion_matrix(model, X, y, 3)
    np.savetxt(
        "exports/mean_confusion_matrix_ratio.csv",
        mcm,
        fmt='%.2f',
        delimiter=";")


def clear_dir(dir_to_clear):
    for root, _, files in os.walk(dir_to_clear):
        for file_to_rm in files:
            os.remove(os.path.join(root, file_to_rm))


if __name__ == '__main__':
    if not os.path.exists('exports'):
        os.makedirs('exports')
    else:
        clear_dir('exports')

    temp_bounds_imgs_gen()
    grain_samples_imgs_gen()
    blob_detection_compare_plots_gen()
    blob_ratio_table_gen()
    blob_count_plots_gen()
    blob_analysis_plots_gen()
    neural_network_test_table_gen()
    neural_network_validation_table_gen()
    neural_network_trainig_plots_gen()
    network_comparison_table_gen()
    confusion_matrix_table_gen()

    plt.show()
