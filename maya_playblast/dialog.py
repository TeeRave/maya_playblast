# coding=utf-8
from __future__ import print_function, absolute_import

import logging
import os
import traceback

import pymel.core as pm
from PySide2 import QtCore
from PySide2 import QtWidgets
from shotgun import SG_Shot
from shotgun import context

from . import playblast


class MBlastUI(QtWidgets.QDialog):

    def __init__(self, parent=None):
        super(MBlastUI, self).__init__(parent)

        self.debian_version = None
        self.minimum_supported_version = 10

        shot = SG_Shot(context.entity.id)
        try:
            self.cut_in, self.cut_out = shot.cut_in, shot.cut_out
            self.cut_in_cut_out_available = True
        except AttributeError:
            self.cut_in_cut_out_available = False
            logging.info('cut-in/cut-out not found')

        if not self.objectName():
            self.setObjectName(u"PlayblastWindow")

        self.setWindowTitle("Playblast")

        self.resize(450, 130)

        self.gridLayout_parent = QtWidgets.QGridLayout(self)
        self.gridLayout_parent.setObjectName(u"gridLayout_parent")
        self.gridLayout = QtWidgets.QGridLayout()
        self.gridLayout.setObjectName(u"gridLayout")
        self.gridLayout.setContentsMargins(10, 10, 10, 0)

        self.frame_range_lb = QtWidgets.QLabel("Frame Range:")
        self.frame_range_lb.setObjectName(u"frame_range_lb")
        self.gridLayout.addWidget(self.frame_range_lb, 1, 0, 1, 2)

        self.start_frame_sb = QtWidgets.QSpinBox(self)
        self.start_frame_sb.setObjectName(u"start_frame_sb")
        self.start_frame_sb.setWrapping(False)
        self.start_frame_sb.setFrame(True)
        self.start_frame_sb.setAlignment(QtCore.Qt.AlignLeft | QtCore.Qt.AlignTrailing | QtCore.Qt.AlignVCenter)
        self.start_frame_sb.setButtonSymbols(QtWidgets.QAbstractSpinBox.NoButtons)
        self.start_frame_sb.setAccelerated(False)
        self.start_frame_sb.setMaximum(9999)
        self.start_frame_sb.setValue(pm.env.minTime)
        self.gridLayout.addWidget(self.start_frame_sb, 1, 2, 1, 1)
        self.start_frame_sb.setFocusPolicy(QtCore.Qt.ClickFocus)

        self.previous_start_frame = self.start_frame_sb.value()

        self.end_frame_sb = QtWidgets.QSpinBox(self)
        self.end_frame_sb.setObjectName(u"end_frame_sb")
        self.end_frame_sb.setAlignment(QtCore.Qt.AlignLeft | QtCore.Qt.AlignTrailing | QtCore.Qt.AlignVCenter)
        self.end_frame_sb.setButtonSymbols(QtWidgets.QAbstractSpinBox.NoButtons)
        self.end_frame_sb.setMaximum(9999)
        self.end_frame_sb.setValue(pm.env.maxTime)
        self.gridLayout.addWidget(self.end_frame_sb, 1, 3, 1, 1)
        self.end_frame_sb.setFocusPolicy(QtCore.Qt.ClickFocus)

        self.previous_end_frame = self.end_frame_sb.value()

        self.fit_to_cutin_cutout_cb = QtWidgets.QCheckBox("Fit to Cut-in/Cut-out")
        self.fit_to_cutin_cutout_cb.setObjectName(u"fit_to_cutin_cutout_cb")
        self.gridLayout.addWidget(self.fit_to_cutin_cutout_cb, 1, 4, 1, 4)
        self.fit_to_cutin_cutout_cb.toggled.connect(self.update_frame_ranges)
        if not self.cut_in_cut_out_available:
            self.fit_to_cutin_cutout_cb.setEnabled(False)

        self.after_playblast_lb = QtWidgets.QLabel("After playblast:")
        self.after_playblast_lb.setObjectName(u"after_playblast_lb")
        self.gridLayout.addWidget(self.after_playblast_lb, 2, 0, 1, 2)

        self.post_action_rb_group = QtWidgets.QButtonGroup()

        self.open_in_upload_version_rb = QtWidgets.QRadioButton("Open in upload_version")
        self.open_in_upload_version_rb.setObjectName(u"open_in_upload_version_rb")
        self.open_in_upload_version_rb.setChecked(True)
        self.gridLayout.addWidget(self.open_in_upload_version_rb, 2, 2, 1, 2, alignment=QtCore.Qt.AlignHCenter)
        self.post_action_rb_group.addButton(self.open_in_upload_version_rb)

        self.open_folder_rb = QtWidgets.QRadioButton("Open Folder")
        self.open_folder_rb.setObjectName(u"open_folder_rb")
        self.gridLayout.addWidget(self.open_folder_rb, 2, 4, 1, 2, alignment=QtCore.Qt.AlignHCenter)
        self.post_action_rb_group.addButton(self.open_folder_rb)

        self.do_nothing_rb = QtWidgets.QRadioButton("Do nothing")
        self.do_nothing_rb.setObjectName(u"do_nothing_rb")
        self.gridLayout.addWidget(self.do_nothing_rb, 2, 6, 1, 2, alignment=QtCore.Qt.AlignHCenter)
        self.post_action_rb_group.addButton(self.do_nothing_rb)

        self.after_playblast_lb = QtWidgets.QLabel("Version Upload Software:")
        self.after_playblast_lb.setObjectName(u"version_upload_software_lb")
        self.gridLayout.addWidget(self.after_playblast_lb, 3, 0, 1, 2)

        self.mv_rb_group = QtWidgets.QButtonGroup()

        self.upload_version_2_rb = QtWidgets.QRadioButton("upload_version2")
        self.upload_version_2_rb.setObjectName(u"upload_version_2_rb")
        self.upload_version_2_rb.clicked.connect(self.update_availability)
        self.gridLayout.addWidget(self.upload_version_2_rb, 3, 2, 1, 2, alignment=QtCore.Qt.AlignHCenter)
        self.mv_rb_group.addButton(self.upload_version_2_rb)
        self.upload_version_2_rb.setChecked(True)

        self.upload_version_1_rb = QtWidgets.QRadioButton("upload_version1")
        self.upload_version_1_rb.setObjectName(u"upload_version_1_rb")
        self.upload_version_1_rb.clicked.connect(self.update_availability)
        self.gridLayout.addWidget(self.upload_version_1_rb, 3, 4, 1, 2, alignment=QtCore.Qt.AlignHCenter)
        self.mv_rb_group.addButton(self.upload_version_1_rb)

        self.playblast_btn = QtWidgets.QPushButton("Playblast")
        self.playblast_btn.setObjectName(u"playblast_btn")
        self.gridLayout.addWidget(self.playblast_btn, 4, 0, 1, 8, alignment=QtCore.Qt.AlignBottom)
        self.playblast_btn.setDefault(True)
        self.playblast_btn.setAutoDefault(True)
        self.playblast_btn.setFocus()
        self.playblast_btn.clicked.connect(self.start)

        self.outdated_notice_lb = None

        self.gridLayout_parent.addLayout(self.gridLayout, 0, 0, 1, 1)

        self.use_legacy = False

        self.is_old_debian = self.debian_version_is_old()

        if not self.is_old_debian:
            self.use_legacy = False
            self.upload_version_1_rb.setEnabled(False)
            self.upload_version_2_rb.setChecked(True)
        if self.is_old_debian:
            self.use_legacy = True
            self.upload_version_1_rb.setChecked(True)
            self.add_outdated_notice()
            self.set_enabled_elements(self.get_widget_children(exclude=[self.upload_version_1_rb]), state=False)

    def update_frame_ranges(self):
        if self.fit_to_cutin_cutout_cb.isChecked():
            self.previous_start_frame = self.start_frame_sb.value()
            self.previous_end_frame = self.end_frame_sb.value()
            self.start_frame_sb.setValue(self.cut_in)
            self.end_frame_sb.setValue(self.cut_out)
        else:
            self.start_frame_sb.setValue(self.previous_start_frame)
            self.end_frame_sb.setValue(self.previous_end_frame)

    def get_ui_parameters(self):
        return dict(start_frame=self.start_frame_sb.value(),
                    end_frame=self.end_frame_sb.value(),
                    open_in_mv_afterward=self.open_in_upload_version_rb.isChecked(),
                    open_folder_afterward=self.open_folder_rb.isChecked())

    def get_widget_children(self, exclude=None):
        if exclude is None:
            exclude = []
        widget_children = []
        qt_types = [QtWidgets.QSpinBox, QtWidgets.QCheckBox, QtWidgets.QRadioButton]
        for qt_type in qt_types:
            c = self.findChildren(qt_type)
            for child in c:
                if child not in exclude:
                    widget_children.append(child)
        return widget_children

    def update_availability(self):
        if self.upload_version_1_rb.isChecked():
            self.set_enabled_elements(self.get_widget_children(exclude=[self.upload_version_1_rb, self.upload_version_2_rb]),
                                      state=False)
            self.use_legacy = True
        else:
            self.set_enabled_elements(self.get_widget_children(),
                                      state=True)
            self.use_legacy = False

    def debian_version_is_old(self):
        """
        Проверка того, нужно ли использовать Legacy плейбласт и upload_version1 соответственно.
        Новый плейбласт (реализованный в этом модуле) и upload_version2 поддерживают только Debian 10 и новее

        Returns
        -------
        is_old: bool
        """
        import platform
        is_old = False
        if platform.system() == 'Linux':
            distro, version, id = platform.linux_distribution()
            self.debian_version = float(version)
            if distro == 'debian' and float(version) < self.minimum_supported_version:
                is_old = True
        return is_old

    @staticmethod
    def set_enabled_elements(widgets, state):
        for widget in widgets:
            widget.setEnabled(state)

    def add_outdated_notice(self):
        btn_index = self.gridLayout.indexOf(self.playblast_btn)
        btn_row, btn_col, btn_col_span, btn_row_span = self.gridLayout.getItemPosition(btn_index)
        self.gridLayout.takeAt(btn_index)
        warning_text = 'Warning: {} does not support Debian {}'.format(self.upload_version_2_rb.text(),
                                                                       self.debian_version)
        self.outdated_notice_lb = QtWidgets.QLabel(warning_text)
        self.gridLayout.addWidget(self.outdated_notice_lb, btn_row, btn_col, 2, btn_row_span,
                                  alignment=QtCore.Qt.AlignHCenter)
        self.gridLayout.addWidget(self.playblast_btn, btn_row + 2, btn_col, btn_row_span, btn_row_span,
                                  alignment=QtCore.Qt.AlignBottom)

    def start(self, *args, **kwargs):
        if self.use_legacy:
            logging.info('Debian < {}. Using old playblast + upload_version...'.format(self.minimum_supported_version))
            import maya_playblast_legacy
            maya_playblast_legacy.run()
            self.close()
            return
        if not pm.sceneName():
            QtWidgets.QMessageBox.warning(pm.ui.PyUI('MayaWindow').asQtObject(),
                                          'Playblast', 'Please save your scene first.')
            return
        # get arguments from UI
        ui_kwargs = self.get_ui_parameters()
        # start the playblast
        try:
            sequence_path = playblast.run(**ui_kwargs)
            if not sequence_path:
                return
        except Exception as e:
            pm.PopupError(str(e))
            logging.exception('Playblast failed')
            return
        # post action
        if ui_kwargs.get('open_in_mv_afterward'):
            try:
                logging.info('Sending to upload_version2')
                from upload_version2.utils import launch
                launch(path=sequence_path)
            except Exception as e:
                traceback.print_exc()
                pm.PopupError(str(e))
        elif ui_kwargs.get('open_folder_afterward'):
            logging.info('Opening folder')
            import webbrowser
            webbrowser.open(os.path.dirname(sequence_path))


if __name__ == '__main__':
    # Create and show the form
    dialog = MBlastUI(parent=pm.ui.PyUI('MayaWindow').asQtObject())
    main_dialog = dialog.show()
