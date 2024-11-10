# SPDX-FileCopyrightText: 2023 Jean-Baptiste Mardelle <jb@kdenlive.org>
# SPDX-FileCopyrightText: 2024 Julius Künzel <julius.kuenzel@kde.org>
# SPDX-License-Identifier: GPL-3.0-only OR LicenseRef-KDE-Accepted-GPL

from pathlib import Path
from typing import Optional
from xml.dom.minidom import Text, parse


class RenderProject:
    def __init__(self, projectPath: Path, referencePath=None):
        if not projectPath.is_file():
            raise Exception(f"The Kdenlive project {projectPath!r} does not exist!")

        self.projectPath = projectPath

        self.propRenderProfile: Optional[str] = None
        self.propRenderUrl: Optional[str] = None

        self.propRenderProfile, self.propRenderUrl, self.propFps = self._extractRenderInfo()

        self.renderOutputMissing = False
        self.renderLog: Optional[str] = None
        self.renderErrorLog: Optional[str] = None

    def _extractRenderInfo(self) -> tuple[str, str]:
        document = parse(str(self.projectPath))
        pl = document.getElementsByTagName("playlist")
        renderProfile = ""
        renderUrl = ""
        for node in pl:
            pl_id = node.getAttribute("id")
            if pl_id == "main_bin":
                props = node.getElementsByTagName("property")
                for prop in props:
                    prop_name = prop.getAttribute("name")
                    if prop_name == "kdenlive:docproperties.renderprofile":
                        assert prop.firstChild
                        assert isinstance(prop.firstChild, Text)
                        renderProfile = prop.firstChild.data
                    if prop_name == "kdenlive:docproperties.renderurl":
                        assert prop.firstChild
                        assert isinstance(prop.firstChild, Text)
                        renderUrl = prop.firstChild.data
                break

        pr = document.getElementsByTagName("profile")

        fps = 25
        if pr:
            fps = int(pr[0].getAttribute("frame_rate_num"))

        if not fps:
            fps = 25

        # print("GOT PROFILE INFO:", renderProfile, " = ", renderUrl, flush=True)
        return (renderProfile, renderUrl, fps)

    @property
    def name(self) -> str:
        return self.projectPath.name

    def __str__(self):
        return self.name

    @property
    def renderFilename(self) -> str:
        if self.propRenderUrl:
            return Path(self.projectPath.name).stem + Path(self.propRenderUrl).suffix
        else:
            return Path(self.projectPath.name).stem + ".mp4"

    @property
    def allowFaliure(self) -> bool:
        return self.renderFilename == "mix-luma.mp4"
