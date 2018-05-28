#! /usr/bin/env python

import sys
sys.path.append('/usr/share/inkscape/extensions')
import inkex
import os
import subprocess
import tempfile
import shutil
import copy
import simplepath, simpletransform
from simplestyle import *

identity_m = [[1.0,0.0,0.0],[0.0,1.0,0.0]]

class Svg2ShenzhenPrepare(inkex.Effect):
    def __init__(self):
        """init the effetc library and get options from gui"""
        inkex.Effect.__init__(self)
        self.OptionParser.add_option("--docwidth", action="store", type="float", dest="docwidth", default=0.0)

        self.bb_width_center = 0
        self.bb_height_center = 0
        self.bb_scaling = 0

    def coordToKicad(self,XYCoord):
        return [
            (XYCoord[0]-self.bb_width_center)/self.bb_scaling,
            (XYCoord[1]-self.bb_height_center)/self.bb_scaling,
        ]

    def setInkscapeScaling(self):

        root = self.document.getroot()
        height = float(root.get('height').replace("mm", ""))
        width = float(root.get('width').replace("mm", ""))

        viewbox = root.attrib['viewBox'].split(' ')
        viewbox_h = float(viewbox[-1])
        viewbox_w = float(viewbox[-2])

        self.doc_width = width
        self.doc_height = height
        self.bb_width_center = viewbox_w/2
        self.bb_height_center = viewbox_h/2
        self.bb_scaling = viewbox_h/height


    def setDocumentSquare(self, width):
        root = self.document.getroot()
        root.attrib['width'] = str(width) + "mm"
        root.attrib['height'] = str(width) + "mm"
        root.attrib['viewBox'] = "0 0 %f %f" % (width, width)


    def createLayer(self, layer_name):
        svg = self.document.xpath('//svg:svg',namespaces=inkex.NSS)[0]
        layer = inkex.etree.SubElement(svg, 'g')
        layer.set(inkex.addNS('label', 'inkscape'), '%s' % layer_name)
        layer.set(inkex.addNS('groupmode', 'inkscape'), 'layer')
        return layer

    def createWhitebg(self):
        rect = inkex.etree.Element(inkex.addNS('rect','svg'))
        rect.set('x', "0")
        rect.set('y', "0")
        rect.set('width', str(self.doc_width/self.bb_scaling))
        rect.set('height', str(self.doc_height/self.bb_scaling))
        style = {'fill' : '#FFFFFF', 'fill-opacity' : '1', 'stroke': 'none'}
        rect.set('style', formatStyle(style))
        return rect

    def prepareDocument(self):
        svg_layers = self.document.xpath('//svg:g[@inkscape:groupmode="layer"]', namespaces=inkex.NSS)
        layers = []

        for layer in svg_layers:
            label_attrib_name = "{%s}label" % layer.nsmap['inkscape']
            if label_attrib_name not in layer.attrib:
                continue
            layer_label = layer.attrib[label_attrib_name]
            layers.append(layer_label)

        if ("[fixed] BG" not in layers):
            white_layer = self.createLayer("[fixed] BG")
            white_layer.set(inkex.addNS('insensitive', 'sodipodi'), 'true')
            rect = self.createWhitebg()
            white_layer.append(rect)

        if ("F.Cu" not in layers and "F.Cu-disabled" not in layers):
            self.createLayer("F.Cu")

        if ("B.Cu-disabled" not in layers and "B.Cu" not in layers):
            self.createLayer("B.Cu-disabled")

        if ("B.Adhes-disabled" not in layers and "B.Adhes" not in layers):
            self.createLayer("B.Adhes-disabled")

        if ("F.Adhes-disabled" not in layers and "F.Adhes" not in layers):
            self.createLayer("F.Adhes-disabled")

        if ("B.Paste-disabled" not in layers and "B.Paste" not in layers):
            self.createLayer("B.Paste-disabled")

        if ("F.Paste-disabled" not in layers and "F.Paste" not in layers):
            self.createLayer("F.Paste-disabled")

        if ("B.SilkS-disabled" not in layers and "B.SilkS" not in layers):
            self.createLayer("B.SilkS-disabled")

        if ("F.SilkS-disabled" not in layers and "F.SilkS" not in layers):
            self.createLayer("F.SilkS-disabled")

        if ("B.Mask-disabled" not in layers and "B.Mask" not in layers):
            self.createLayer("B.Mask-disabled")

        if ("F.Mask-disabled" not in layers and "F.Mask" not in layers):
            self.createLayer("F.Mask-disabled")

        if ("Dwgs.User-disabled" not in layers and "Dwgs.User" not in layers):
            self.createLayer("Dwgs.User-disabled")

        if ("Cmts.User-disabled" not in layers and "Cmts.User" not in layers):
            self.createLayer("Cmts.User-disabled")

        if ("Eco1.User-disabled" not in layers and "Eco1.User" not in layers):
            self.createLayer("Eco1.User-disabled")

        if ("Eco2.User-disabled" not in layers and "Eco2.User" not in layers):
            self.createLayer("Eco2.User-disabled")

        if ("Edge.Cuts" not in layers):
            self.createLayer("Edge.Cuts")

        if ("Margin-disabled" not in layers and "Margin" not in layers):
            self.createLayer("Margin-disabled")

        if ("B.CrtYd-disabled" not in layers and "B.CrtYd" not in layers):
            self.createLayer("B.CrtYd-disabled")

        if ("F.CrtYd-disabled" not in layers and "F.CrtYd" not in layers):
            self.createLayer("F.CrtYd-disabled")

        if ("B.Fab-disabled" not in layers and "B.Fab" not in layers):
            self.createLayer("B.Fab-disabled")

        if ("F.Fab-disabled" not in layers and "F.Fab" not in layers):
            self.createLayer("F.Fab-disabled")

        if ("Drill" not in layers):
            self.createLayer("Drill")

    def setDocumentGrid(self):
        doc_view = self.document.xpath('//sodipodi:namedview',namespaces=inkex.NSS)[0]
        doc_view.attrib['borderlayer'] = "true"
        doc_view.attrib['showgrid'] = "true"

        grid = inkex.etree.Element(inkex.addNS('grid','inkscape'))
        grid.set('spacingx', '2.54')
        grid.set('spacingy', '2.54')
        grid.set('empspacing', '1')
        grid.set('type', 'xygrid')
        grid.set('units', 'mm')

        doc_view.append(grid)

    def setDefaultUnits(self):
        # just a convenience so that when you draw you will use mm by default
        namedview = self.document.find('sodipodi:namedview', namespaces=inkex.NSS)
        namedview.attrib['{http://www.inkscape.org/namespaces/inkscape}document-units'] = 'mm'

    def effect(self):
        self.setDocumentSquare(self.options.docwidth)
        self.setInkscapeScaling()
        self.prepareDocument()
        self.setDocumentGrid()
        self.setDefaultUnits()


    def export_layers(self, dest, show):
        """
        Export selected layers of SVG to the file `dest`.
        :arg  str   dest:  path to export SVG file.
        :arg  list  hide:  layers to hide. each element is a string.
        :arg  list  show:  layers to show. each element is a string.
        """
        doc = copy.deepcopy(self.document)
        for layer in doc.xpath('//svg:g[@inkscape:groupmode="layer"]', namespaces=inkex.NSS):
            layer.attrib['style'] = 'display:none'
            id = layer.attrib["id"]
            if id in show:
                layer.attrib['style'] = 'display:inline'

        doc.write(dest)

    def get_layers(self, src):
        svg_layers = self.document.xpath('//svg:g[@inkscape:groupmode="layer"]', namespaces=inkex.NSS)
        layers = []

        for layer in svg_layers:
            label_attrib_name = "{%s}label" % layer.nsmap['inkscape']
            if label_attrib_name not in layer.attrib:
                continue

            layer_id = layer.attrib["id"]
            layer_label = layer.attrib[label_attrib_name]

            layer_label_name = layer_label
            inkex.debug(layer_label_name)

            if  layer_label_name in self.layer_map.iterkeys():
                layer_type = "export"
                layer_label = layer_label_name
            elif layer_label.lower().startswith("[fixed] "):
                layer_type = "fixed"
                layer_label = layer_label[8:]
            else:
                continue

            layers.append([layer_id, layer_label, layer_type])

        return layers


def _main():
    e = Svg2ShenzhenPrepare()
    e.affect()
    exit()

if __name__ == "__main__":
    _main()
