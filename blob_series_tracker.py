'''Track and count number of blobs in thermal images of grains.'''

import matplotlib.pyplot as plt
import matplotlib.patches as mpatches
from skimage.color import rgb2gray

from img_processing import crop_ui, full_prepare, load_img_series
from blob_finder import find_blobs


def patch_plot_legend_outside(colors, labels):
    '''
    Make given plots share their legend entry and place legend upper right.
    '''
    legend = [mpatches.Patch(color=color, label=label)
              for color, label in zip(colors, labels)]
    plt.legend(handles=legend, loc='upper right', bbox_to_anchor=(1, 1))


def inside_circle(x, y, a, b, r):
    '''
    Return True if point (x, y) lies inside circle
    with center of (a, b) and radius r.
    '''
    return (x - a) * (x - a) + (y - b) * (y - b) < r * r


def find_remaining_blobs(new_blobs, old_blobs):
    '''
    Return list of blobs present in both lists, where blob is considered same
    if is in proximity of 2 times it's radius.
    '''
    remaining = []
    for new_blob in new_blobs:
        yn, xn, _ = new_blob
        for old_blob in old_blobs:
            yo, xo, ro = old_blob
            if inside_circle(xn, yn, xo, yo, 2 * ro):
                remaining.append(new_blob)
    return unique(remaining)


def unique(multilist):
    '''Get list without repeating values.'''
    return list(set(tuple(i) for i in multilist))


def find_blob_series(imgs, only_remaining=True):
    '''
    Return list of list of blobs found in each of given images.
    '''
    stages = []
    remaining = None
    for img in imgs:
        new_blobs = find_blobs(img)
        if remaining is not None and only_remaining:
            remaining = find_remaining_blobs(new_blobs, remaining)
        else:
            remaining = new_blobs
        stages.append(remaining)
    return stages


def ratio_of_remaining_blobs_in_stages(stages):
    '''
    In each stage calculate ratio of remaining blobs to their initial number.
    '''
    num_of_blobs = [len(stage) for stage in stages]
    return [remaining / num_of_blobs[0] for remaining in num_of_blobs]


def count_blobs_with_all_methods(X):
    '''
    Get number of blobs in all images in X data set
    using three ways of counting.
    '''
    # Option one: all
    Xa = [[
        len(stage)
        for stage in find_blob_series(img_series, only_remaining=False)
    ] for img_series in X]

    # Option two: remaining
    Xr = [[
        len(stage) for stage in find_blob_series(img_series)
    ] for img_series in X]

    # Option three: remaining ratio
    Xp = [
        ratio_of_remaining_blobs_in_stages(find_blob_series(img_series))
        for img_series in X
    ]
    return Xa, Xr, Xp


def main():
    '''Demo blob tracking with various ways of counting blobs.'''
    # Load images
    imgs = load_img_series('img/104_E5R')
    # Prepare images for processing
    imgs_prep = [full_prepare(img) for img in imgs]
    # Prepare cropped images for displaying
    imgs_crop = [crop_ui(rgb2gray(img)) for img in imgs]

    # Find blobs for stages of cooling with preserving only remainig ones
    stages_rem = find_blob_series(imgs_prep)

    # Map stages on first image
    colors = ('blue', 'blueviolet', 'magenta', 'crimson', 'red')
    _, ax = plt.subplots(1)
    plt.title("Blobs detection with DoH")
    plt.imshow(imgs_crop[0], cmap=plt.get_cmap('gray'))
    for stage, color in zip(stages_rem, colors):
        for blob in stage:
            y, x, r = blob
            c = plt.Circle((x, y), r, color=color, linewidth=0.75, fill=False)
            ax.add_patch(c)
    labels = ('Minute 0', 'Minute 1', 'Minute 2', 'Minute 3', 'Minute 4')
    patch_plot_legend_outside(colors, labels)
    print(ratio_of_remaining_blobs_in_stages(stages_rem))

    # Show stages on subplots
    _, ax = plt.subplots(2, 3, figsize=(12, 7))
    ax = ax.flatten()

    for idx, (stage, img) in enumerate(zip(stages_rem, imgs_crop)):
        ax[idx].imshow(img, cmap=plt.get_cmap('gray'))
        ax[idx].set_title("Minute: {}, blobs: {}".format(idx, len(stage)))
        for blob in stage:
            y, x, r = blob
            c = plt.Circle((x, y), r, color='r', linewidth=0.75, fill=False)
            ax[idx].add_patch(c)
    ax[-1].set_axis_off()
    plt.tight_layout()

    # Find all blobs for every stage of cooling
    stages_all = find_blob_series(imgs_prep, only_remaining=False)

    # Show stages on subplots
    _, ax = plt.subplots(2, 3, figsize=(12, 7))
    ax = ax.flatten()

    for idx, (stage, img) in enumerate(zip(stages_all, imgs_crop)):
        ax[idx].imshow(img, cmap=plt.get_cmap('gray'))
        ax[idx].set_title("Minute: {}, blobs: {}".format(idx, len(stage)))
        for blob in stage:
            y, x, r = blob
            c = plt.Circle((x, y), r, color='r', linewidth=0.75, fill=False)
            ax[idx].add_patch(c)
    ax[-1].set_axis_off()
    plt.tight_layout()

    # Show two methods combined to compare
    _, ax = plt.subplots(2, 3, figsize=(10, 7))
    ax = ax.flatten()

    # Show stages on subplots
    loop_set = enumerate(zip(stages_rem, stages_all, imgs_crop))
    for idx, (stage_rem, stage_all, img) in loop_set:
        ax[idx].imshow(img, cmap=plt.get_cmap('gray'))
        ax[idx].set_title("Minute: {}, all blobs: {}, rem blobs: {}".
                          format(idx, len(stage_all), len(stage_rem)))
        for blob_all in stage_all:
            y, x, r = blob_all
            c = plt.Circle((x, y), r, color='b', linewidth=0.75, fill=False)
            ax[idx].add_patch(c)
        for blob_rem in stage_rem:
            y, x, r = blob_rem
            c = plt.Circle((x, y), r, color='r', linewidth=0.75, fill=False)
            ax[idx].add_patch(c)
    ax[-1].set_axis_off()
    plt.tight_layout()

    plt.show()


if __name__ == "__main__":
    main()
