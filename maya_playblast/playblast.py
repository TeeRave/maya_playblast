# coding=utf-8
from __future__ import absolute_import, print_function, unicode_literals, division

import glob
import logging
import os
import re
import sys

import pymel.core as pm
from PySide2.QtWidgets import QMessageBox
from shotgun import context
from maya import cmds
from resource_collector.maya_resource_collector import MayaResourceCollector


def run(**kwargs):
    try:
        return do_playblast(**kwargs)
    except Exception as e:
        QMessageBox.critical(pm.ui.PyUI('MayaWindow').asQtObject(), "Error", str(e))
        logging.exception('Playblast failed')


def do_playblast(**kwargs):
    camera = kwargs.get('camera') or get_current_camera()
    save_path = kwargs.get('output_path') or get_output_path(**kwargs)
    image_path_mask = render_playblast(camera, save_path, **kwargs)
    if not image_path_mask:
        QMessageBox.warning(pm.ui.PyUI('MayaWindow').asQtObject(), 'Playblast', 'Playblast interrupted.')
        return
    save_meta_data(image_path_mask, **kwargs)
    return image_path_mask


def get_current_camera():
    """
    Find and return the correct render camera shape

    Returns
    -------
    nt.Camera
    """
    # query playblast panel
    panel_name = pm.ui.PyUI(pm.playblast(ae=True))
    # query playblast camera
    cam_shape = panel_name.getCamera()
    if cam_shape.type() != 'camera':
        cam_shape = cam_shape.getShape()
    return cam_shape


def get_output_path(**kwargs):
    """
    Playblast frames render path using pattern <save_dir>/<entity_path>_%4d.<ext>

    Parameters
    ----------
    kwargs

    Returns
    -------
    str
    """
    task_id = context.task.id
    playblast_fullpath = get_playblast_path(task_id, **kwargs)
    return playblast_fullpath


def get_playblast_path(extension='jpg', frame_mask=False, **kwargs):
    entity_name = context.task.entity.full_name
    user_dir = context.get_userdir('flipbook')
    if not os.path.isdir(user_dir):
        os.makedirs(user_dir)

    all_versions = []
    for path in sorted(os.listdir(user_dir)):
        if re.match(r"v\d{3}$", path):
            all_versions.append(path)
    if all_versions:
        new_version_digits = str(int(''.join(re.findall(r'(\d)', all_versions[-1]))) + 1)
    else:
        new_version_digits = '1'
    new_version_string = 'v' + new_version_digits.zfill(3)

    prefix = '{entity_full_name}_{dep_short_name}_{version}'.format(entity_full_name=entity_name,
                                                                    dep_short_name=context.task.step.short_name,
                                                                    version=new_version_string)
    base_path = os.path.join(user_dir, new_version_string.zfill(3), prefix)
    if frame_mask:
        frame_padding = kwargs.get('frame_padding', 4)
        # create a path string formatted like "/drive/path/to/image.%0<number>d.<extension>"
        playblast_path = base_path + '.%' + str(frame_padding).zfill(2) + 'd.' + extension
    else:
        playblast_path = base_path

    return playblast_path


temp_data = {}


def save_temp_scene():
    """
    Save scene to task temp dir

    Returns
    -------
    saved_current_scene_path : str
    """
    task_id = context.task.id
    # out path
    tmp_path = os.path.join(context.USER_TEMPDIR, 'tsk_{}'.format(task_id))

    if not os.path.exists(tmp_path):
        try:
            os.makedirs(tmp_path)
            os.chmod(tmp_path, 0o777)
        except Exception as e:
            logging.error('Can`t create temp folder "{}": {}'.format(tmp_path, e))

    current_name = pm.sceneName()
    saved_current_scene_path = os.path.join(os.path.normpath(tmp_path), current_name.basename())

    # make way for a new temp scene by deleting the old one if it already exists
    if os.path.isfile(saved_current_scene_path):
        try:
            os.remove(saved_current_scene_path)
        except Exception as e:
            logging.error('Old scene was not removed: {}'.format(e))
    # save
    try:
        cmds.file(rename=saved_current_scene_path)
        cmds.file(save=True, force=True)
    except Exception as e:
        logging.error('Scene not saved: {}'.format(e))
        return
    # restore name
    cmds.file(rename=current_name)
    return saved_current_scene_path


def render_playblast(render_camera, output_path, resolution=None, **kwargs):
    """
    The Playblast render itself.
    Before rendering all necessary settings need to be set, and reverted after Playblast completion

    Parameters
    ----------
    render_camera
    output_path
    resolution
    """
    temp_scene_path = save_temp_scene()
    if temp_scene_path:
        temp_data['temp_scene'] = temp_scene_path
        sys.stdout.write('Temp Scene saved to:\n{}\n'.format(temp_scene_path))
    else:
        sys.stdout.write('Temp Scene not created.')

    # get correct resolution from camera data
    playblast_resolution = resolution \
        or get_dailies_resolution_from_camera() or get_dailies_resolution_from_sg()

    w, h = playblast_resolution
    sys.stdout.write('# playblast | SG Resolution:\n{}\n'.format(playblast_resolution))

    sys.stdout.write('# playblasting to:\n{}\n'.format(output_path))

    # prepare kwargs.
    force_overwrite = kwargs.get('force_overwrite', True)
    sequence_time = kwargs.get('sequence_time', False)
    clear_cache = kwargs.get('clear_cache', True)
    off_screen = kwargs.get('off_screen', True)
    frame_padding = kwargs.get('frame_padding', 4)
    percent = kwargs.get('percent', 100)
    compression = kwargs.get('compression', 'jpg')
    quality = kwargs.get('quality', 100)
    viewer = kwargs.get('viewer', False)
    width_height = kwargs.get('width_height', (w, h))
    options = kwargs.get('options', False)
    show_ornaments = kwargs.get('show_ornaments', False)
    start_frame = kwargs.get('start_frame', None)
    end_frame = kwargs.get('end_frame', None)

    # store the camera that was active before
    initial_camera = pm.lookThru(q=True)
    # switch to the one specified for the playblast
    pm.lookThru(render_camera)

    # store initial timeline range to revert to later
    start_frame_initial = pm.env.minTime
    end_frame_initial = pm.env.maxTime
    # if start and end frames were modified, temporarily set the timeline to them
    if (start_frame != start_frame_initial) or (end_frame != end_frame_initial):
        pm.env.minTime = start_frame
        pm.env.maxTime = end_frame

    # begin playblast render and get its image path pattern.
    img_name_pattern = cmds.playblast(format='image',
                                      filename=output_path,
                                      forceOverwrite=force_overwrite,
                                      sequenceTime=sequence_time,
                                      clearCache=clear_cache,
                                      offScreen=off_screen,
                                      framePadding=frame_padding,
                                      percent=percent,
                                      compression=compression,
                                      quality=quality,
                                      viewer=viewer,
                                      widthHeight=width_height,
                                      options=options,
                                      showOrnaments=show_ornaments)

    # reverting to the timeline settings that were set before the playblast
    if start_frame and end_frame:
        pm.env.minTime = start_frame_initial
        pm.env.maxTime = end_frame_initial

    # revert to the camera that was active before
    pm.lookThru(initial_camera)

    # checking whether the playblast was successful
    if img_name_pattern:
        first_frame_path = sorted(glob.glob(img_name_pattern.replace('#' * frame_padding, '*')))[0]
        sys.stdout.write('# playblast | first frame path:\n{}\n'.format(first_frame_path))
        return first_frame_path.replace('\\', '/')


def save_meta_data(resource_path, **kwargs):
    """
    Saving the json file containing metadata

    Parameters
    ----------
    resource_path: str
    """

    meta = MayaResourceCollector(
        resource_path,
        content_type=kwargs.get('content_type') or 'animation_scene',
        temp_scene=temp_data.get('temp_scene'),
        publish_scene=temp_data.get('temp_scene'))
    meta.collect(**kwargs)


def get_dailies_resolution_from_sg():
    """
    Getting a tuple of the width & height from the "Version Resolution" field in Shotgun

    Returns
    -------
    tuple
    """
    # getting the version resolution field's data from SG
    dailies_resolution_str = context.project.sg_dailies_resolution
    # конвертируем его значения в список float
    # parse & convert its values
    dailies_resolution_width, dailies_resolution_height = [float(value) for value in dailies_resolution_str.split('x')]
    return int(dailies_resolution_width), int(dailies_resolution_height)


def get_dailies_resolution_from_camera(cam=None):
    if not cam:
        active_panel = pm.ui.PyUI(pm.playblast(activeEditor=True))
        cam = active_panel.getCamera()
    if pm.hasAttr(cam, 'Resolution'):
        cam_res_attr = pm.getAttr(cam + '.Resolution')
        dailies_resolution_width, dailies_resolution_height = [float(value) for value in cam_res_attr.split('x')]
        return int(dailies_resolution_width), int(dailies_resolution_height)
