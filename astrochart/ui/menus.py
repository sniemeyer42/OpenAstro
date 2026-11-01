#    This file is part of openastro.org.
#
#    OpenAstro.org is free software: you can redistribute it and/or modify
#    it under the terms of the GNU General Public License as published by
#    the Free Software Foundation, either version 3 of the License, or
#    (at your option) any later version.
#
#    OpenAstro.org is distributed in the hope that it will be useful,
#    but WITHOUT ANY WARRANTY; without even the implied warranty of
#    MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
#    GNU General Public License for more details.
#
#    You should have received a copy of the GNU General Public License
#    along with OpenAstro.org.  If not, see <http://www.gnu.org/licenses/>.
"""
Menu definitions (Gtk.Builder XML) of the main window
"""

MENU_XML = """
<interface>
  <menu id="MenuBar">
    <submenu>
    <attribute name="label" translatable="yes">Application</attribute>
      <section>
        <item>
          <attribute name="action">win.maximize</attribute>
          <attribute name="label" translatable="yes">Maximize</attribute>
        </item>
      </section>
      <section>
        <item>
          <attribute name="label" translatable="yes">About</attribute>
          <attribute name="action">win.about</attribute>
        </item>
        <item>
          <attribute name="label" translatable="yes">Quit</attribute>
          <attribute name="action">app.quit</attribute>
        </item>
      </section>
    </submenu>
    <submenu>
      <attribute name="label" translatable="yes">Settings</attribute>
      <section>
        <item>
          <attribute name="label" translatable="yes">Set Location</attribute>
          <attribute name="action">win.settingsLocation</attribute>
        </item>
        <item>
          <attribute name="label" translatable="yes">Configuration</attribute>
          <attribute name="action">win.settingsConfiguration</attribute>
        </item>
        <item>
          <attribute name="label" translatable="yes">Aspects</attribute>
          <attribute name="action">win.settingsAspects</attribute>
        </item>
        <item>
          <attribute name="label" translatable="yes">Planets &amp; Angles</attribute>
          <attribute name="action">win.settingsPlanets</attribute>
        </item>
      </section>
    </submenu>
    <submenu>
      <attribute name="label" translatable="yes">Chart Types</attribute>
      <section>
        <item>
          <attribute name="label" translatable="yes">Radix Chart</attribute>
          <attribute name="action">win.specialRadix</attribute>
        </item>
        <item>
          <attribute name="label" translatable="yes">Transit Chart</attribute>
          <attribute name="action">win.specialTransit</attribute>
        </item>
      </section>
      <section>
        <item>
          <attribute name="label" translatable="yes">Synastry Chart</attribute>
          <attribute name="action">win.chartType</attribute>
          <attribute name="target">Synastry</attribute>
        </item>
        <item>
          <attribute name="label" translatable="yes">Composite Chart</attribute>
          <attribute name="action">win.chartType</attribute>
          <attribute name="target">Composite</attribute>
        </item>
        <item>
          <attribute name="label" translatable="yes">Combine Chart</attribute>
          <attribute name="action">win.chartType</attribute>
          <attribute name="target">Combine</attribute>
        </item>
      </section>
      <section>
        <item>
          <attribute name="label" translatable="yes">Solar Return</attribute>
          <attribute name="action">win.specialSolar</attribute>
        </item>
        <item>
          <attribute name="label" translatable="yes">Solar Progression</attribute>
          <attribute name="action">win.specialProgression</attribute>
        </item>
      </section>
    </submenu>
    <submenu>
      <attribute name="label" translatable="yes">Tables</attribute>
        <item>
          <attribute name="label" translatable="yes">Monthly Timeline</attribute>
          <attribute name="action">win.tableMonthlyTimeline</attribute>
        </item>
        <item>
          <attribute name="label" translatable="yes">Cusp Aspects</attribute>
          <attribute name="action">win.tableCuspAspects</attribute>
        </item>
    </submenu>
    <submenu>
      <attribute name="label" translatable="yes">Zoom</attribute>
        <section>
          <item>
            <attribute name="label" translatable="yes">Out</attribute>
            <attribute name="action">win.zoom</attribute>
            <attribute name="target">zOut</attribute>
          </item>
          <item>
            <attribute name="label" translatable="yes">80%</attribute>
            <attribute name="action">win.zoom</attribute>
            <attribute name="target">z80</attribute>
          </item>
          <item>
            <attribute name="label" translatable="yes">100%</attribute>
            <attribute name="action">win.zoom</attribute>
            <attribute name="target">z100</attribute>
            <attribute name="accel">1</attribute>
          </item>
          <item>
            <attribute name="label" translatable="yes">150%</attribute>
            <attribute name="action">win.zoom</attribute>
            <attribute name="target">z150</attribute>
          </item>
          <item>
            <attribute name="label" translatable="yes">200%</attribute>
            <attribute name="action">win.zoom</attribute>
            <attribute name="target">z200</attribute>
          </item>
          <item>
            <attribute name="label" translatable="yes">In</attribute>
            <attribute name="action">win.zoom</attribute>
            <attribute name="target">zIn</attribute>
          </item>
        </section>
    </submenu>
    <submenu>
      <attribute name="label" translatable="yes">Extra</attribute>
        <item>
          <attribute name="label" translatable="yes">Export Database</attribute>
          <attribute name="action">win.exportdb</attribute>
        </item>
        <item>
          <attribute name="label" translatable="yes">Import Database</attribute>
          <attribute name="action">win.importdb</attribute>
        </item>
    </submenu>
    <submenu>
      <attribute name="label" translatable="yes">Help</attribute>
        <item>
          <attribute name="label" translatable="yes">About</attribute>
          <attribute name="action">win.about</attribute>
        </item>
    </submenu>
  </menu>
</interface>
"""

CHART_XML = """
<interface>
  <menu id="ChartUI">
    <section>
      <item>
        <attribute name="label" translatable="yes">New</attribute>
        <attribute name="action">win.newChart</attribute>
      </item>
      <item>
        <attribute name="label" translatable="yes">Open</attribute>
        <attribute name="action">win.openChart</attribute>
      </item>
      <item>
        <attribute name="label" translatable="yes">Save</attribute>
        <attribute name="action">win.saveChart</attribute>
      </item>
    </section>
    <submenu>
      <attribute name="label" translatable="yes">Import</attribute>
      <section>
        <item>
          <attribute name="label" translatable="yes">Oroboros (*.xml)</attribute>
          <attribute name="action">win.import</attribute>
          <attribute name="target">importOroboros</attribute>
        </item>
        <item>
          <attribute name="label" translatable="yes">Astrolog (*.dat)</attribute>
          <attribute name="action">win.import</attribute>
          <attribute name="target">importAstrolog</attribute>
        </item>
        <item>
          <attribute name="label" translatable="yes">Skylendar (*.skif)</attribute>
          <attribute name="action">win.import</attribute>
          <attribute name="target">importSkylendar</attribute>
        </item>
        <item>
          <attribute name="label" translatable="yes">Zet8 Dbase (*.zbs)</attribute>
          <attribute name="action">win.import</attribute>
          <attribute name="target">importZet8</attribute>
        </item>
      </section>
    </submenu>
    <submenu>
      <attribute name="label" translatable="yes">Export</attribute>
      <section>
        <item>
          <attribute name="label" translatable="yes">PNG file</attribute>
          <attribute name="action">win.export</attribute>
          <attribute name="target">pngfile</attribute>
        </item>
        <item>
          <attribute name="label" translatable="yes">JPG file</attribute>
          <attribute name="action">win.export</attribute>
          <attribute name="target">jpgfile</attribute>
        </item>
        <item>
          <attribute name="label" translatable="yes">SVG file</attribute>
          <attribute name="action">win.export</attribute>
          <attribute name="target">svgfile</attribute>
        </item>
        <item>
          <attribute name="label" translatable="yes">PDF file</attribute>
          <attribute name="action">win.export</attribute>
          <attribute name="target">pdffile</attribute>
        </item>
      </section>
    </submenu>
    <section>
      <item>
        <attribute name="label" translatable="yes">Close</attribute>
        <attribute name="action">win.close</attribute>
      </item>
    </section>
  </menu>
</interface>
"""

EVENT_XML = """
<interface>
  <menu id="EventUI">
    <section>
      <item>
        <attribute name="label" translatable="yes">Edit Event</attribute>
        <attribute name="action">win.eventData</attribute>
      </item>
      <item>
        <attribute name="label" translatable="yes">Open Database</attribute>
        <attribute name="action">win.openDatabase</attribute>
      </item>
    </section>
    <section>
      <item>
        <attribute name="label" translatable="yes">Open Famous People Database</attribute>
        <attribute name="action">win.openDataFamous</attribute>
      </item>
    </section>
  </menu>
</interface>
"""

BEGIN_XML = """<?xml version="1.0" encoding="UTF-8"?>
<interface>
  <menu id="UpdateUI">
    <section>
"""
E_ITEM = """      <item>
        <attribute name="label" translatable="yes">empty</attribute>
        <attribute name="action">win.empty</attribute>
      </item>"""
M_ITEM = """      <item>
        <attribute name="label" translatable="yes">$label</attribute>
        <attribute name="action">win.$db</attribute>
        <attribute name="target" type="i">$idx</attribute>
      </item>"""
END_XML = """
    </section>
  </menu>
</interface>
"""
