# coding=utf-8
"""
Usage:

>>> import maya_playblast
>>> maya_playblast.show()
"""
from __future__ import absolute_import
import pymel.core as pm


def close_and_delete_all_children(parent, child_py_type_object, child_object_name):
    # find, close & delete the previous Maya Playblast window instance(s)
    for child in parent.findChildren(child_py_type_object, child_object_name):
        child.close()
        child.deleteLater()


def show():
    """
    Maya Playblast dialog open
    """
    from . import dialog
    from PySide2.QtWidgets import QDialog
    maya_window_object = pm.ui.PyUI('MayaWindow').asQtObject()
    close_and_delete_all_children(maya_window_object, QDialog, 'PlayblastWindow')
    # create a new window
    maya_playblast_window = dialog.MBlastUI(parent=maya_window_object)
    maya_playblast_window.show()
