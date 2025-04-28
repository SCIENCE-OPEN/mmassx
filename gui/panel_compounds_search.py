# -------------------------------------------------------------------------
#     Copyright (C) 2005-2013 Martin Strohalm <www.mmass.org>

#     This program is free software; you can redistribute it and/or modify
#     it under the terms of the GNU General Public License as published by
#     the Free Software Foundation; either version 3 of the License, or
#     (at your option) any later version.

#     This program is distributed in the hope that it will be useful,
#     but WITHOUT ANY WARRANTY; without even the implied warranty of
#     MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE. See the
#     GNU General Public License for more details.

#     Complete text of GNU GPL can be found in the file LICENSE.TXT in the
#     main directory of the program.
# -------------------------------------------------------------------------

# load libs
from operator import add
import threading
import math
import wx

# load modules
from ids import *
import mwx
import images
import config
import libs
import mspy
import doc

from gui.panel_match import panelMatch


# FLOATING PANEL WITH COUPOUND SEARCH TOOL
# ----------------------------------------

# $$
FORMULAS = {
    '[M+Li]+':'Li',
    '[M-H2O+H]+':'H-2O-1',
    '[M-H2O-H]-':'H-2O-1',
    '[+ACN+H]+':'CH3CN',
    '[+MeOH+H]+':'CH3OH',
    '[M-H]-': 'H',
    '[M+H]+': 'H',

    '(13)C1':'C{13}C-1',
    '(13)C2':'C{13}2C-2',
    '(13)C3':'C{13}3C-3',
    '(13)C4':'C{13}4C-4',
    '(13)C5':'C{13}5C-5',
    '(13)C6':'C{13}6C-6',
    '(15)N1':'N{15}N-1',
    '(15)N2':'N{15}2N-2',
    '(15)N3':'N{15}3N-3',
    '(15)N4':'N{15}4N-4',
    '(15)N5':'N{15}5N-5',
    '(15)N6':'N{15}6N-6',
    '(15)N7':'N{15}7N-7',
    '(15)N8':'N{15}8N-8',
    '(15)N9':'N{15}9N-9',

    '[M+Cl]-':'Cl',
    '[M+Na-2H]-':'Na',
    '[M+K-2H]-':'K',
    '[M-CH3]-':'C-1H-3',
    '[M-C3H10N]-':'C-3H-10N-1',
    '[M-C5H12N]-':'C-5H-12N-1',

    '[M+Na]+':'Na',
    '[M+K]+':'K',
    '[M+NH4]+':'NH4',

    '[2M-H]-':'H',
    '[2M+Cl]-':'Cl',
    '[2M+Na-2H]-':'Na',
    '[2M+K-2H]-':'K',

    '[2M+H]+':'H',
    '[2M+Na]+':'Na',
    '[2M+K]+':'K',
    '[2M+NH4]+':'NH4',

    '[M+FMP10]+':'C20H13N',
    '[M+2FMP10]+':'C40H26N2',
    '[M+2FMP10-CH3]+':'C39H24N2',

    '[M+AMPP]+':'C12H10N2O-1',
    '[M+2AMPP]+':'C24H20N4O-2',
    '[M+3AMPP]+':'C36H30N6O-3',
};

# $$
class CurrentCompound():
    # 0 name, 1 m/z, 2 z, 3 adduct, 4 formula, 5 error, 6 matches, 7 measured m/z
    def __init__(self, name, mz, z, adduct, formula, isotope=None, error=None, measuredMz=None, matches = []):
        self.name = name
        self.mz = mz
        self.z = z
        self.adduct = adduct
        self.isotope = isotope
        self.formula = formula
        self.error = error
        self.measuredMz = measuredMz
        self.matches = matches

class panelCompoundsSearch(wx.MiniFrame):
    """Compounds search tool."""
    
    def __init__(self, parent, tool='compounds'):
        wx.MiniFrame.__init__(self, parent, -1, 'Compounds Search', size=(400, 300), style=wx.DEFAULT_FRAME_STYLE & ~ (wx.RESIZE_BOX | wx.MAXIMIZE_BOX))
        
        self.parent = parent
        self.matchPanel = None
        
        self.processing = None
        
        self.currentTool = tool
        self.currentDocument = None
        self.currentCompounds = []
        
        self._compoundsFilter = 0
        
        # make gui items
        self.makeGUI()
        wx.EVT_CLOSE(self, self.onClose)
        
        # select default tool
        self.onToolSelected(tool=self.currentTool)
    # ----
    
    
    def makeGUI(self):
        """Make panel gui."""
        
        # make toolbar
        toolbar = self.makeToolbar()
        controlbar = self.makeControlbar()
        
        # make ADDU
        self.makeCompoundsList()
        gauge = self.makeGaugePanel()
        
        # pack elements
        self.mainSizer = wx.BoxSizer(wx.VERTICAL)
        self.mainSizer.Add(toolbar, 0, wx.EXPAND, 0)
        self.mainSizer.Add(controlbar, 0, wx.EXPAND, 0)
        self.mainSizer.Add(self.compoundsList, 1, wx.EXPAND|wx.ALL, mwx.LISTCTRL_NO_SPACE)
        self.mainSizer.Add(gauge, 0, wx.EXPAND, 0)
        
        # hide gauge
        self.mainSizer.Hide(3)
        
        # fit layout
        self.mainSizer.Fit(self)
        self.SetSizer(self.mainSizer)
        self.SetMinSize(self.GetSize())
    # ----
    
    
    def makeToolbar(self):
        """Make toolbar."""
        
        # init toolbar
        panel = mwx.bgrPanel(self, -1, images.lib['bgrToolbar'], size=(-1, mwx.TOOLBAR_HEIGHT))
        
        # make tools
        self.compounds_butt = wx.BitmapButton(panel, ID_compoundsSearchCompounds, images.lib['compoundsSearchCompoundsOff'], size=(mwx.TOOLBAR_TOOLSIZE), style=wx.BORDER_NONE)
        self.compounds_butt.SetToolTip(wx.ToolTip("Compounds search"))
        self.compounds_butt.Bind(wx.EVT_BUTTON, self.onToolSelected)
        
        self.formula_butt = wx.BitmapButton(panel, ID_compoundsSearchFormula, images.lib['compoundsSearchFormulaOff'], size=(mwx.TOOLBAR_TOOLSIZE), style=wx.BORDER_NONE)
        self.formula_butt.SetToolTip(wx.ToolTip("Formula search"))
        self.formula_butt.Bind(wx.EVT_BUTTON, self.onToolSelected)
        
        self.tool_label = wx.StaticText(panel, -1, "Compounds:")
        self.tool_label.SetFont(wx.SMALL_FONT)
        
        choices = libs.compounds.keys()
        choices.sort()
        choices.insert(0,'Compounds lists')
        self.compounds_choice = wx.Choice(panel, -1, choices=choices, size=(250, mwx.SMALL_CHOICE_HEIGHT))
        self.compounds_choice.Select(0)
        self.compounds_choice.Bind(wx.EVT_CHOICE, self.onGenerate)
        
        self.formula_value = wx.TextCtrl(panel, -1, "", size=(270,-1))
        
        # make buttons
        self.generate_butt = wx.Button(panel, -1, "Generate", size=(-1, mwx.SMALL_BUTTON_HEIGHT))
        self.generate_butt.Bind(wx.EVT_BUTTON, self.onGenerate)
        
        self.match_butt = wx.Button(panel, -1, "Match", size=(-1, mwx.SMALL_BUTTON_HEIGHT))
        self.match_butt.Bind(wx.EVT_BUTTON, self.onMatch)
        
        self.annotate_butt = wx.Button(panel, -1, "Annotate", size=(-1, mwx.SMALL_BUTTON_HEIGHT))
        self.annotate_butt.Bind(wx.EVT_BUTTON, self.onAnnotate)
        
        # pack elements
        self.toolbar = wx.BoxSizer(wx.HORIZONTAL)
        self.toolbar.AddSpacer(mwx.TOOLBAR_LSPACE)
        self.toolbar.Add(self.compounds_butt, 0, wx.ALIGN_CENTER_VERTICAL)
        self.toolbar.Add(self.formula_butt, 0, wx.ALIGN_CENTER_VERTICAL|wx.LEFT, mwx.BUTTON_SIZE_CORRECTION)
        self.toolbar.AddSpacer(20)
        self.toolbar.Add(self.tool_label, 0, wx.ALIGN_CENTER_VERTICAL|wx.RIGHT, 5)
        self.toolbar.Add(self.compounds_choice, 0, wx.ALIGN_CENTER_VERTICAL)
        self.toolbar.Add(self.formula_value, 0, wx.ALIGN_CENTER_VERTICAL)
        self.toolbar.AddStretchSpacer()
        self.toolbar.AddSpacer(20)
        self.toolbar.Add(self.generate_butt, 0, wx.ALIGN_CENTER_VERTICAL|wx.RIGHT, 10)
        self.toolbar.Add(self.match_butt, 0, wx.ALIGN_CENTER_VERTICAL|wx.RIGHT, 10)
        self.toolbar.Add(self.annotate_butt, 0, wx.ALIGN_CENTER_VERTICAL)
        self.toolbar.AddSpacer(mwx.TOOLBAR_RSPACE)
        
        self.toolbar.Hide(5)
        self.toolbar.Hide(6)
        
        mainSizer = wx.BoxSizer(wx.VERTICAL)
        mainSizer.Add(self.toolbar, 1, wx.EXPAND)
        panel.SetSizer(mainSizer)
        mainSizer.Fit(panel)
        
        return panel
    # ----
    
    
    def makeControlbar(self):
        """Make controlbar."""
        
        # init toolbar
        panel = mwx.bgrPanel(self, -1, images.lib['bgrControlbar'], size=(-1, mwx.CONTROLBAR_HEIGHT))
        
        # make elements
        massType_label = wx.StaticText(panel, -1, "Mass:")
        massType_label.SetFont(wx.SMALL_FONT)
    
        self.massTypeMo_radio = wx.RadioButton(panel, -1, "Mo", style=wx.RB_GROUP)
        self.massTypeMo_radio.SetFont(wx.SMALL_FONT)
        self.massTypeMo_radio.SetValue(True)
        
        self.massTypeAv_radio = wx.RadioButton(panel, -1, "Av")
        self.massTypeAv_radio.SetFont(wx.SMALL_FONT)
        self.massTypeAv_radio.SetValue(config.compoundsSearch['massType'])
        
        maxCharge_label = wx.StaticText(panel, -1, "Max charge:")
        maxCharge_label.SetFont(wx.SMALL_FONT)
        
        self.maxCharge_value = wx.TextCtrl(panel, -1, str(config.compoundsSearch['maxCharge']), size=(30, mwx.SMALL_TEXTCTRL_HEIGHT), validator=mwx.validator('int'))
        self.maxCharge_value.SetFont(wx.SMALL_FONT)
        
        self.radicals_check = wx.CheckBox(panel, -1, "M*")
        self.radicals_check.SetFont(wx.SMALL_FONT)
        self.radicals_check.SetValue(config.compoundsSearch['radicals'])
        
        adducts_label = wx.StaticText(panel, -1, "Adducts:")
        adducts_label.SetFont(wx.SMALL_FONT)

        
        
        self.adductACN_check = wx.CheckBox(panel, -1, "[+ACN+H]+")
        self.adductACN_check.SetFont(wx.SMALL_FONT)
        self.adductACN_check.SetValue(config.compoundsSearch['adducts'].count('[+ACN+H]+'))
        
        self.adductMeOH_check = wx.CheckBox(panel, -1, "[+MeOH+H]+")
        self.adductMeOH_check.SetFont(wx.SMALL_FONT)
        self.adductMeOH_check.SetValue(config.compoundsSearch['adducts'].count('[+MeOH+H]+'))


    	#fm edited
        Labeling_label = wx.StaticText(panel, -1, "Labeling")
        Labeling_label.SetFont(wx.SMALL_FONT)

        self.adduct13C1_check = wx.CheckBox(panel, -1, "(13)C1")
        self.adduct13C1_check.SetFont(wx.SMALL_FONT)
        self.adduct13C1_check.SetValue(config.compoundsSearch['isotopes'].count('(13)C1'))

        self.adduct13C2_check = wx.CheckBox(panel, -1, "(13)C2")
        self.adduct13C2_check.SetFont(wx.SMALL_FONT)
        self.adduct13C2_check.SetValue(config.compoundsSearch['isotopes'].count('(13)C2'))

        self.adduct13C3_check = wx.CheckBox(panel, -1, "(13)C3")
        self.adduct13C3_check.SetFont(wx.SMALL_FONT)
        self.adduct13C3_check.SetValue(config.compoundsSearch['isotopes'].count('(13)C3'))

        self.adduct13C4_check = wx.CheckBox(panel, -1, "(13)C4")
        self.adduct13C4_check.SetFont(wx.SMALL_FONT)
        self.adduct13C4_check.SetValue(config.compoundsSearch['isotopes'].count('(13)C4'))

        self.adduct13C5_check = wx.CheckBox(panel, -1, "(13)C5")
        self.adduct13C5_check.SetFont(wx.SMALL_FONT)
        self.adduct13C5_check.SetValue(config.compoundsSearch['isotopes'].count('(13)C5'))

        self.adduct13C6_check = wx.CheckBox(panel, -1, "(13)C6")
        self.adduct13C6_check.SetFont(wx.SMALL_FONT)
        self.adduct13C6_check.SetValue(config.compoundsSearch['isotopes'].count('(13)C6'))

        self.adduct15N1_check = wx.CheckBox(panel, -1, "(15)N1")
        self.adduct15N1_check.SetFont(wx.SMALL_FONT)
        self.adduct15N1_check.SetValue(config.compoundsSearch['isotopes'].count('(15)N1'))

        self.adduct15N2_check = wx.CheckBox(panel, -1, "(15)N2")
        self.adduct15N2_check.SetFont(wx.SMALL_FONT)
        self.adduct15N2_check.SetValue(config.compoundsSearch['isotopes'].count('(15)N2'))

        self.adduct15N3_check = wx.CheckBox(panel, -1, "(15)N3")
        self.adduct15N3_check.SetFont(wx.SMALL_FONT)
        self.adduct15N3_check.SetValue(config.compoundsSearch['isotopes'].count('(15)N3'))

        self.adduct15N4_check = wx.CheckBox(panel, -1, "(15)N4")
        self.adduct15N4_check.SetFont(wx.SMALL_FONT)
        self.adduct15N4_check.SetValue(config.compoundsSearch['isotopes'].count('(15)N4'))

        self.adduct15N5_check = wx.CheckBox(panel, -1, "(15)N5")
        self.adduct15N5_check.SetFont(wx.SMALL_FONT)
        self.adduct15N5_check.SetValue(config.compoundsSearch['isotopes'].count('(15)N5'))

        self.adduct15N6_check = wx.CheckBox(panel, -1, "(15)N6")
        self.adduct15N6_check.SetFont(wx.SMALL_FONT)
        self.adduct15N6_check.SetValue(config.compoundsSearch['isotopes'].count('(15)N6'))

        self.adduct15N7_check = wx.CheckBox(panel, -1, "(15)N7")
        self.adduct15N7_check.SetFont(wx.SMALL_FONT)
        self.adduct15N7_check.SetValue(config.compoundsSearch['isotopes'].count('(15)N7'))

        self.adduct15N8_check = wx.CheckBox(panel, -1, "(15)N8")
        self.adduct15N8_check.SetFont(wx.SMALL_FONT)
        self.adduct15N8_check.SetValue(config.compoundsSearch['isotopes'].count('(15)N8'))

        self.adduct15N9_check = wx.CheckBox(panel, -1, "(15)N9")
        self.adduct15N9_check.SetFont(wx.SMALL_FONT)
        self.adduct15N9_check.SetValue(config.compoundsSearch['isotopes'].count('(15)N9'))

        NEG1M_label = wx.StaticText(panel, -1, "NEG 1M:")
        NEG1M_label.SetFont(wx.SMALL_FONT)

        self.adductM_Cl_check = wx.CheckBox(panel, -1, "[M+Cl]-")
        self.adductM_Cl_check.SetFont(wx.SMALL_FONT)
        self.adductM_Cl_check.SetValue(config.compoundsSearch['adducts'].count('[M+Cl]-'))

        self.adductM_NA_2H_check = wx.CheckBox(panel, -1, "[M+Na-2H]-")
        self.adductM_NA_2H_check.SetFont(wx.SMALL_FONT)
        self.adductM_NA_2H_check.SetValue(config.compoundsSearch['adducts'].count('[M+Na-2H]-'))

        self.adductM_K_2H_check = wx.CheckBox(panel, -1, "[M+K-2H]-")
        self.adductM_K_2H_check.SetFont(wx.SMALL_FONT)
        self.adductM_K_2H_check.SetValue(config.compoundsSearch['adducts'].count('[M+K-2H]-'))


        self.adductM_H2O_H_minus_check = wx.CheckBox(panel, -1, "[M-H2O-H]-")
        self.adductM_H2O_H_minus_check.SetFont(wx.SMALL_FONT)
        self.adductM_H2O_H_minus_check.SetValue(config.compoundsSearch['adducts'].count('[M-H2O-H]-'))


        PCPA_label = wx.StaticText(panel, -1, "(L)-PC/PA loss:")
        PCPA_label.SetFont(wx.SMALL_FONT)

        self.adduct_M_CH3_check = wx.CheckBox(panel, -1, "[M-CH3]-")
        self.adduct_M_CH3_check.SetFont(wx.SMALL_FONT)
        self.adduct_M_CH3_check.SetValue(config.compoundsSearch['adducts'].count('[M-CH3]-'))

        self.adduct_M_C3H10N_check = wx.CheckBox(panel, -1, "[M-C3H10N]-")
        self.adduct_M_C3H10N_check.SetFont(wx.SMALL_FONT)
        self.adduct_M_C3H10N_check.SetValue(config.compoundsSearch['adducts'].count('[M-C3H10N]-'))

        self.adduct_M_C5H12N_check = wx.CheckBox(panel, -1, "[M-C5H12N]-")
        self.adduct_M_C5H12N_check.SetFont(wx.SMALL_FONT)
        self.adduct_M_C5H12N_check.SetValue(config.compoundsSearch['adducts'].count('[M-C5H12N]-'))

        POS1M_label = wx.StaticText(panel, -1, "POS 1M:")
        POS1M_label.SetFont(wx.SMALL_FONT)

        self.adduct_M_Na_check = wx.CheckBox(panel, -1, "[M+Na]+")
        self.adduct_M_Na_check.SetFont(wx.SMALL_FONT)
        self.adduct_M_Na_check.SetValue(config.compoundsSearch['adducts'].count('[M+Na]+'))

        self.adduct_M_K_check = wx.CheckBox(panel, -1, "[M+K]+")
        self.adduct_M_K_check.SetFont(wx.SMALL_FONT)
        self.adduct_M_K_check.SetValue(config.compoundsSearch['adducts'].count('[M+K]+'))

        self.adductLi_check = wx.CheckBox(panel, -1, "[M+Li]+")
        self.adductLi_check.SetFont(wx.SMALL_FONT)
        self.adductLi_check.SetValue(config.compoundsSearch['adducts'].count('[M+Li]+'))

        self.adduct_M_NH4_check = wx.CheckBox(panel, -1, "[M+NH4]+")
        self.adduct_M_NH4_check.SetFont(wx.SMALL_FONT)
        self.adduct_M_NH4_check.SetValue(config.compoundsSearch['adducts'].count('[M+NH4]+'))


        self.adductM_H2O_H_plus_check = wx.CheckBox(panel, -1, "[M-H2O+H]+")
        self.adductM_H2O_H_plus_check.SetFont(wx.SMALL_FONT)
        self.adductM_H2O_H_plus_check.SetValue(config.compoundsSearch['adducts'].count('[M-H2O+H]+'))


        NEG2M_label = wx.StaticText(panel, -1, "NEG 2M:")
        NEG2M_label.SetFont(wx.SMALL_FONT)

        self.adduct_M2_NEG_H_check = wx.CheckBox(panel, -1, "[2M-H]-")
        self.adduct_M2_NEG_H_check.SetFont(wx.SMALL_FONT)
        self.adduct_M2_NEG_H_check.SetValue(config.compoundsSearch['adducts'].count('[2M-H]-'))

        self.adduct_M2_Cl_check = wx.CheckBox(panel, -1, "[2M+Cl]-")
        self.adduct_M2_Cl_check.SetFont(wx.SMALL_FONT)
        self.adduct_M2_Cl_check.SetValue(config.compoundsSearch['adducts'].count('[2M+Cl]-'))

        self.adduct_M2_Na_2H_check = wx.CheckBox(panel, -1, "[2M+Na-2H]-")
        self.adduct_M2_Na_2H_check.SetFont(wx.SMALL_FONT)
        self.adduct_M2_Na_2H_check.SetValue(config.compoundsSearch['adducts'].count('[2M+Na-2H]-'))

        self.adduct_M2_K_2H_check = wx.CheckBox(panel, -1, "[2M+K-2H]-")
        self.adduct_M2_K_2H_check.SetFont(wx.SMALL_FONT)
        self.adduct_M2_K_2H_check.SetValue(config.compoundsSearch['adducts'].count('[2M+K-2H]-'))

        POS2M_label = wx.StaticText(panel, -1, "POS 2M:")
        POS2M_label.SetFont(wx.SMALL_FONT)

        self.adduct_M2_H_check = wx.CheckBox(panel, -1, "[2M+H]+")
        self.adduct_M2_H_check.SetFont(wx.SMALL_FONT)
        self.adduct_M2_H_check.SetValue(config.compoundsSearch['adducts'].count('[2M+H]+'))

        self.adduct_M2_Na_check = wx.CheckBox(panel, -1, "[2M+Na]+")
        self.adduct_M2_Na_check.SetFont(wx.SMALL_FONT)
        self.adduct_M2_Na_check.SetValue(config.compoundsSearch['adducts'].count('[2M+Na]+'))

        self.adduct_M2_K_check = wx.CheckBox(panel, -1, "[2M+K]+")
        self.adduct_M2_K_check.SetFont(wx.SMALL_FONT)
        self.adduct_M2_K_check.SetValue(config.compoundsSearch['adducts'].count('[2M+K]+'))

        self.adduct_M2_NH4_check = wx.CheckBox(panel, -1, "[2M+NH4]+")
        self.adduct_M2_NH4_check.SetFont(wx.SMALL_FONT)
        self.adduct_M2_NH4_check.SetValue(config.compoundsSearch['adducts'].count('[2M+NH4]+'))

        FMP10_label = wx.StaticText(panel, -1, "Derivatization FMP10:")
        FMP10_label.SetFont(wx.SMALL_FONT)

        self.adduct_FMP10_check = wx.CheckBox(panel, -1, "[M+FMP10]+")
        self.adduct_FMP10_check.SetFont(wx.SMALL_FONT)
        self.adduct_FMP10_check.SetValue(config.compoundsSearch['adducts'].count('[M+FMP10]+'))

        self.adduct_2FMP10_check = wx.CheckBox(panel, -1, "[M+2FMP10]+")
        self.adduct_2FMP10_check.SetFont(wx.SMALL_FONT)
        self.adduct_2FMP10_check.SetValue(config.compoundsSearch['adducts'].count('[M+2FMP10]+'))

        self.adduct_2FMP10_CH3_check = wx.CheckBox(panel, -1, "[M+2FMP10-CH3]+")
        self.adduct_2FMP10_CH3_check.SetFont(wx.SMALL_FONT)
        self.adduct_2FMP10_CH3_check.SetValue(config.compoundsSearch['adducts'].count('[M+2FMP10-CH3]+'))

        AMPP_label = wx.StaticText(panel, -1, "Derivatization AMPP:")
        AMPP_label.SetFont(wx.SMALL_FONT)

        self.adduct_AMPP_check = wx.CheckBox(panel, -1, "[M+AMPP]+")
        self.adduct_AMPP_check.SetFont(wx.SMALL_FONT)
        self.adduct_AMPP_check.SetValue(config.compoundsSearch['adducts'].count('[M+AMPP]+'))

        self.adduct_2AMPP_check = wx.CheckBox(panel, -1, "[M+2AMPP]+")
        self.adduct_2AMPP_check.SetFont(wx.SMALL_FONT)
        self.adduct_2AMPP_check.SetValue(config.compoundsSearch['adducts'].count('[M+2AMPP]+'))

        self.adduct_3AMPP_check = wx.CheckBox(panel, -1, "[M+3AMPP]+")
        self.adduct_3AMPP_check.SetFont(wx.SMALL_FONT)
        self.adduct_3AMPP_check.SetValue(config.compoundsSearch['adducts'].count('[M+3AMPP]+'))
        #fm edited en

        # pack elements
        sizer = wx.BoxSizer(wx.HORIZONTAL)
        sizer.AddSpacer(mwx.CONTROLBAR_LSPACE)
        sizer.Add(massType_label, 0, wx.ALIGN_CENTER_VERTICAL|wx.RIGHT, 5)
        sizer.Add(self.massTypeMo_radio, 0, wx.ALIGN_CENTER_VERTICAL|wx.RIGHT, 5)
        sizer.Add(self.massTypeAv_radio, 0, wx.ALIGN_CENTER_VERTICAL)
        sizer.AddSpacer(20)
        sizer.Add(maxCharge_label, 0, wx.ALIGN_CENTER_VERTICAL|wx.RIGHT, 5)
        sizer.Add(self.maxCharge_value, 0, wx.ALIGN_CENTER_VERTICAL|wx.RIGHT, 5)
        sizer.Add(self.radicals_check, 0, wx.ALIGN_CENTER_VERTICAL)
        sizer.AddSpacer(20)
        sizer.Add(adducts_label, 0, wx.ALIGN_CENTER_VERTICAL|wx.RIGHT, 5)
        sizer.Add(self.adductACN_check, 0, wx.ALIGN_CENTER_VERTICAL|wx.RIGHT, 5)
        sizer.Add(self.adductMeOH_check, 0, wx.ALIGN_CENTER_VERTICAL)
        
        #fm edited
        sizer1 = wx.BoxSizer(wx.HORIZONTAL)
        sizer1.Add(Labeling_label, 0, wx.ALIGN_CENTER_VERTICAL|wx.RIGHT, 5)
        sizer1.Add(self.adduct13C1_check, 0, wx.ALIGN_CENTER_VERTICAL)
        sizer1.AddSpacer(mwx.CONTROLBAR_RSPACE)
        sizer1.Add(self.adduct13C2_check, 0, wx.ALIGN_CENTER_VERTICAL)
        sizer1.AddSpacer(mwx.CONTROLBAR_RSPACE)
        sizer1.Add(self.adduct13C3_check, 0, wx.ALIGN_CENTER_VERTICAL)
        sizer1.AddSpacer(mwx.CONTROLBAR_RSPACE)		
        sizer1.Add(self.adduct13C4_check, 0, wx.ALIGN_CENTER_VERTICAL)
        sizer1.AddSpacer(mwx.CONTROLBAR_RSPACE)
        sizer1.Add(self.adduct13C5_check, 0, wx.ALIGN_CENTER_VERTICAL)
        sizer1.AddSpacer(mwx.CONTROLBAR_RSPACE)
        sizer1.Add(self.adduct13C6_check, 0, wx.ALIGN_CENTER_VERTICAL)
        sizer1.AddSpacer(mwx.CONTROLBAR_RSPACE)
        sizer1.Add(self.adduct15N1_check, 0, wx.ALIGN_CENTER_VERTICAL)
        sizer1.AddSpacer(mwx.CONTROLBAR_RSPACE)
        sizer1.Add(self.adduct15N2_check, 0, wx.ALIGN_CENTER_VERTICAL)
        sizer1.AddSpacer(mwx.CONTROLBAR_RSPACE)
        sizer1.Add(self.adduct15N3_check, 0, wx.ALIGN_CENTER_VERTICAL)
        sizer1.AddSpacer(mwx.CONTROLBAR_RSPACE)
        sizer1.Add(self.adduct15N4_check, 0, wx.ALIGN_CENTER_VERTICAL)
        sizer1.AddSpacer(mwx.CONTROLBAR_RSPACE)
        sizer1.Add(self.adduct15N5_check, 0, wx.ALIGN_CENTER_VERTICAL)
        sizer1.AddSpacer(mwx.CONTROLBAR_RSPACE)
        sizer1.Add(self.adduct15N6_check, 0, wx.ALIGN_CENTER_VERTICAL)
        sizer1.AddSpacer(mwx.CONTROLBAR_RSPACE)
        sizer1.Add(self.adduct15N7_check, 0, wx.ALIGN_CENTER_VERTICAL)
        sizer1.AddSpacer(mwx.CONTROLBAR_RSPACE)
        sizer1.Add(self.adduct15N8_check, 0, wx.ALIGN_CENTER_VERTICAL)
        sizer1.AddSpacer(mwx.CONTROLBAR_RSPACE)
        sizer1.Add(self.adduct15N9_check, 0, wx.ALIGN_CENTER_VERTICAL)

        sizer2 = wx.BoxSizer(wx.HORIZONTAL)
        sizer2.Add(NEG1M_label, 0, wx.ALIGN_CENTER_VERTICAL|wx.RIGHT, 5)
        sizer2.Add(self.adductM_Cl_check, 0, wx.ALIGN_CENTER_VERTICAL)
        sizer2.AddSpacer(mwx.CONTROLBAR_RSPACE)
        sizer2.Add(self.adductM_NA_2H_check, 0, wx.ALIGN_CENTER_VERTICAL)
        sizer2.AddSpacer(mwx.CONTROLBAR_RSPACE)
        sizer2.Add(self.adductM_K_2H_check, 0, wx.ALIGN_CENTER_VERTICAL)
        sizer2.AddSpacer(mwx.CONTROLBAR_RSPACE)
        sizer2.Add(self.adductM_H2O_H_minus_check, 0, wx.ALIGN_CENTER_VERTICAL|wx.RIGHT, 5)
        sizer2.AddSpacer(mwx.CONTROLBAR_RSPACE)
        sizer2.Add(PCPA_label, 0, wx.ALIGN_CENTER_VERTICAL|wx.RIGHT, 5)
        sizer2.Add(self.adduct_M_CH3_check, 0, wx.ALIGN_CENTER_VERTICAL)
        sizer2.AddSpacer(mwx.CONTROLBAR_RSPACE)
        sizer2.Add(self.adduct_M_C3H10N_check, 0, wx.ALIGN_CENTER_VERTICAL)
        sizer2.AddSpacer(mwx.CONTROLBAR_RSPACE)
        sizer2.Add(self.adduct_M_C5H12N_check, 0, wx.ALIGN_CENTER_VERTICAL)
        sizer2.AddSpacer(mwx.CONTROLBAR_RSPACE)
        sizer3 = wx.BoxSizer(wx.HORIZONTAL)
        sizer3.Add(POS1M_label, 0, wx.ALIGN_CENTER_VERTICAL|wx.RIGHT, 5)
        sizer3.Add(self.adduct_M_Na_check, 0, wx.ALIGN_CENTER_VERTICAL)
        sizer3.AddSpacer(mwx.CONTROLBAR_RSPACE)
        sizer3.Add(self.adduct_M_K_check, 0, wx.ALIGN_CENTER_VERTICAL)
        sizer3.AddSpacer(mwx.CONTROLBAR_RSPACE)
        sizer3.Add(self.adductLi_check, 0, wx.ALIGN_CENTER_VERTICAL|wx.RIGHT, 5)
        sizer3.AddSpacer(mwx.CONTROLBAR_RSPACE)
        sizer3.Add(self.adduct_M_NH4_check, 0, wx.ALIGN_CENTER_VERTICAL)
        sizer3.AddSpacer(mwx.CONTROLBAR_RSPACE)
        sizer3.Add(self.adductM_H2O_H_plus_check, 0, wx.ALIGN_CENTER_VERTICAL|wx.RIGHT, 5)
        sizer3.AddSpacer(mwx.CONTROLBAR_RSPACE)
        sizer4 = wx.BoxSizer(wx.HORIZONTAL)
        sizer4.Add(NEG2M_label, 0, wx.ALIGN_CENTER_VERTICAL|wx.RIGHT, 5)
        sizer4.Add(self.adduct_M2_NEG_H_check, 0, wx.ALIGN_CENTER_VERTICAL)
        sizer4.AddSpacer(mwx.CONTROLBAR_RSPACE)
        sizer4.Add(self.adduct_M2_Cl_check, 0, wx.ALIGN_CENTER_VERTICAL)
        sizer4.AddSpacer(mwx.CONTROLBAR_RSPACE)
        sizer4.Add(self.adduct_M2_Na_2H_check, 0, wx.ALIGN_CENTER_VERTICAL)
        sizer4.AddSpacer(mwx.CONTROLBAR_RSPACE)
        sizer4.Add(self.adduct_M2_K_2H_check, 0, wx.ALIGN_CENTER_VERTICAL)
        sizer4.AddSpacer(mwx.CONTROLBAR_RSPACE)
        sizer5 = wx.BoxSizer(wx.HORIZONTAL)
        sizer5.Add(POS2M_label, 0, wx.ALIGN_CENTER_VERTICAL|wx.RIGHT, 5)
        sizer5.Add(self.adduct_M2_H_check, 0, wx.ALIGN_CENTER_VERTICAL)
        sizer5.AddSpacer(mwx.CONTROLBAR_RSPACE)
        sizer5.Add(self.adduct_M2_Na_check, 0, wx.ALIGN_CENTER_VERTICAL)
        sizer5.AddSpacer(mwx.CONTROLBAR_RSPACE)
        sizer5.Add(self.adduct_M2_K_check, 0, wx.ALIGN_CENTER_VERTICAL)
        sizer5.AddSpacer(mwx.CONTROLBAR_RSPACE)
        sizer5.Add(self.adduct_M2_NH4_check, 0, wx.ALIGN_CENTER_VERTICAL)
        sizer5.AddSpacer(mwx.CONTROLBAR_RSPACE)
        sizer6 = wx.BoxSizer(wx.HORIZONTAL)
        sizer6.Add(FMP10_label, 0, wx.ALIGN_CENTER_VERTICAL|wx.RIGHT, 5)
        sizer6.Add(self.adduct_FMP10_check, 0, wx.ALIGN_CENTER_VERTICAL)
        sizer6.AddSpacer(mwx.CONTROLBAR_RSPACE)
        sizer6.Add(self.adduct_2FMP10_check, 0, wx.ALIGN_CENTER_VERTICAL)
        sizer6.AddSpacer(mwx.CONTROLBAR_RSPACE)
        sizer6.Add(self.adduct_2FMP10_CH3_check, 0, wx.ALIGN_CENTER_VERTICAL)
        sizer6.AddSpacer(mwx.CONTROLBAR_RSPACE)
        sizer7 = wx.BoxSizer(wx.HORIZONTAL)
        sizer7.Add(AMPP_label, 0, wx.ALIGN_CENTER_VERTICAL|wx.RIGHT, 5)
        sizer7.Add(self.adduct_AMPP_check, 0, wx.ALIGN_CENTER_VERTICAL)
        sizer7.AddSpacer(mwx.CONTROLBAR_RSPACE)
        sizer7.Add(self.adduct_2AMPP_check, 0, wx.ALIGN_CENTER_VERTICAL)
        sizer7.AddSpacer(mwx.CONTROLBAR_RSPACE)
        sizer7.Add(self.adduct_3AMPP_check, 0, wx.ALIGN_CENTER_VERTICAL)
        sizer7.AddSpacer(mwx.CONTROLBAR_RSPACE)
	    #fm edited end

        mainSizer = wx.BoxSizer(wx.VERTICAL)
        mainSizer.Add(sizer, 1, wx.EXPAND)
        line1 = wx.StaticLine(panel, -1, size=(-1, 4), style=wx.LI_HORIZONTAL)
        mainSizer.Add(line1, 0, wx.EXPAND | wx.ALL, 5)
        mainSizer.Add(sizer1, 1, wx.EXPAND)
        line = wx.StaticLine(panel, -1, size=(-1, 4), style=wx.LI_HORIZONTAL)
        mainSizer.Add(line, 0, wx.EXPAND | wx.ALL, 5)
        mainSizer.Add(sizer2, 1, wx.EXPAND)
        line3 = wx.StaticLine(panel, -1, size=(-1, 4), style=wx.LI_HORIZONTAL)
        mainSizer.Add(line3, 0, wx.EXPAND | wx.ALL, 5)
        mainSizer.Add(sizer3, 1, wx.EXPAND)
        line4 = wx.StaticLine(panel, -1, size=(-1, 4), style=wx.LI_HORIZONTAL)
        mainSizer.Add(line4, 0, wx.EXPAND | wx.ALL, 5)
        mainSizer.Add(sizer4, 1, wx.EXPAND)
        line5 = wx.StaticLine(panel, -1, size=(-1, 4), style=wx.LI_HORIZONTAL)
        mainSizer.Add(line5, 0, wx.EXPAND | wx.ALL, 5)
        mainSizer.Add(sizer5, 1, wx.EXPAND)
        line6 = wx.StaticLine(panel, -1, size=(-1, 4), style=wx.LI_HORIZONTAL)
        mainSizer.Add(line6, 0, wx.EXPAND | wx.ALL, 5)
        mainSizer.Add(sizer6, 1, wx.EXPAND)
        line7 = wx.StaticLine(panel, -1, size=(-1, 4), style=wx.LI_HORIZONTAL)
        mainSizer.Add(line7, 0, wx.EXPAND | wx.ALL, 5)
        mainSizer.Add(sizer7, 1, wx.EXPAND)
        mainSizer.Fit(panel)
        mainSizer.SetSizeHints(panel)
        panel.SetSizer(mainSizer)
        
        return panel
    
    # ----
    
    
    def makeCompoundsList(self):
        """Make compounds list."""
        
        # init list
        self.compoundsList = mwx.sortListCtrl(self, -1, size=(721, 300), style=mwx.LISTCTRL_STYLE_SINGLE)
        self.compoundsList.SetFont(wx.SMALL_FONT)
        self.compoundsList.setSecondarySortColumn(1)
        self.compoundsList.setAltColour(mwx.LISTCTRL_ALTCOLOUR)
        
        # set events
        self.compoundsList.Bind(wx.EVT_LIST_ITEM_SELECTED, self.onItemSelected)
        self.compoundsList.Bind(wx.EVT_LIST_ITEM_ACTIVATED, self.onItemActivated)
        self.compoundsList.Bind(wx.EVT_KEY_DOWN, self.onListKey)
        if wx.Platform == '__WXMAC__':
            self.compoundsList.Bind(wx.EVT_RIGHT_UP, self.onListRMU)
        else:
            self.compoundsList.Bind(wx.EVT_LIST_ITEM_RIGHT_CLICK, self.onListRMU)
        
        # make columns
        self.compoundsList.InsertColumn(0, "Compound", wx.LIST_FORMAT_LEFT)
        self.compoundsList.InsertColumn(1, "Adduct", wx.LIST_FORMAT_CENTER)
        self.compoundsList.InsertColumn(2, "Isotope", wx.LIST_FORMAT_CENTER)
        self.compoundsList.InsertColumn(3, "Formula", wx.LIST_FORMAT_LEFT)
        self.compoundsList.InsertColumn(4, "m/z database", wx.LIST_FORMAT_RIGHT)
        self.compoundsList.InsertColumn(5, "m/z measured", wx.LIST_FORMAT_RIGHT)
        self.compoundsList.InsertColumn(6, "Error (ppm)", wx.LIST_FORMAT_RIGHT)
        self.compoundsList.InsertColumn(7, "z", wx.LIST_FORMAT_CENTER)

        # set column widths
        for col, width in enumerate((200,70,80,200,80,80, 67, 35)):
            self.compoundsList.SetColumnWidth(col, width)
    # ----
    
    
    def makeGaugePanel(self):
        """Make processing gauge."""
        
        panel = wx.Panel(self, -1)
        
        # make elements
        self.gauge = mwx.gauge(panel, -1)
        
        stop_butt = wx.BitmapButton(panel, -1, images.lib['stopper'], style=wx.BORDER_NONE)
        stop_butt.Bind(wx.EVT_BUTTON, self.onStop)
        
        # pack elements
        sizer = wx.BoxSizer(wx.HORIZONTAL)
        sizer.Add(self.gauge, 1, wx.ALIGN_CENTER_VERTICAL)
        sizer.AddSpacer(10)
        sizer.Add(stop_butt, 0, wx.ALIGN_CENTER_VERTICAL)
        
        # fit layout
        mainSizer = wx.BoxSizer(wx.VERTICAL)
        mainSizer.Add(sizer, 1, wx.EXPAND|wx.ALL, mwx.GAUGE_SPACE)
        panel.SetSizer(mainSizer)
        mainSizer.Fit(panel)
        
        return panel
    # ----
    
    
    def onClose(self, evt):
        """Hide this frame."""
        
        # check processing
        if self.processing != None:
            wx.Bell()
            return
        
        # close match panel
        if self.matchPanel:
            self.matchPanel.Close()
        
        # close self
        self.Destroy()
    # ----
    
    
    def onProcessing(self, status=True):
        """Show processing gauge."""
        
        self.gauge.SetValue(0)
        
        if status:
            self.MakeModal(True)
            self.mainSizer.Show(3)
        else:
            self.MakeModal(False)
            self.mainSizer.Hide(3)
            self.processing = None
            mspy.start()
        
        # fit layout
        self.Layout()
        self.mainSizer.Fit(self)
        try: wx.Yield()
        except: pass
    # ----
    
    
    def onStop(self, evt):
        """Cancel current processing."""
        
        if self.processing and self.processing.isAlive():
            mspy.stop()
        else:
            wx.Bell()
    # ----
    
    
    def onToolSelected(self, evt=None, tool=None):
        """Selected tool."""
        
        # get the tool
        if evt != None:
            tool = 'compounds'
            if evt.GetId() == ID_compoundsSearchCompounds:
                tool = 'compounds'
            elif evt.GetId() == ID_compoundsSearchFormula:
                tool = 'formula'

        # set current tool
        self.currentTool = tool
        
        # hide toolbars
        self.toolbar.Hide(5)
        self.toolbar.Hide(6)
        
        # set icons off
        self.compounds_butt.SetBitmapLabel(images.lib['compoundsSearchCompoundsOff'])
        self.formula_butt.SetBitmapLabel(images.lib['compoundsSearchFormulaOff'])
        
        # set panel
        if tool == 'compounds':
            self.SetTitle("Compounds Search")
            self.tool_label.SetLabel('Compounds:')
            self.compounds_butt.SetBitmapLabel(images.lib['compoundsSearchCompoundsOn'])
            self.toolbar.Show(5)
            
        elif tool == 'formula':
            self.SetTitle("Formula Search")
            self.tool_label.SetLabel('Formula:')
            self.formula_butt.SetBitmapLabel(images.lib['compoundsSearchFormulaOn'])
            self.toolbar.Show(6)
        
        # fit layout
        self.toolbar.Layout()
        mwx.layout(self, self.mainSizer)
    # ----
    
    
    def onItemSelected(self, evt):
        """Show selected mass in spectrum canvas."""
        
        currentCompound = self.currentCompounds[evt.GetData()]
        self.parent.updateMassPoints([currentCompound.mz])
    # ----
    
    
    def onItemActivated(self, evt):
        """Show isotopic pattern for selected compound."""
        self.onItemSendToMassCalculator(evt)
    # ----
    
    
    def onItemSendToMassCalculator(self, evt):
        """Show isotopic pattern for selected compound."""

        # get data
        selected = self.compoundsList.getSelected()
        if not selected:
            wx.Bell()
            return

        index = self.compoundsList.GetItemData(selected[0])
        currentCompound = self.currentCompounds[index]

        formula = currentCompound.formula
        charge = currentCompound.z
        radical = currentCompound.adduct

        # send data to Mass Calculator tool
        if radical == 'radical':
            self.parent.onToolsMassCalculator(formula=formula, charge=charge, agentFormula='e', agentCharge=-1)
        else:
            self.parent.onToolsMassCalculator(formula=formula, charge=charge, agentFormula='H', agentCharge=1)
    # ----
    
    
    def onItemCopyFormula(self, evt):
        """Copy selected compound formula into clipboard."""
        
        # get data
        selected = self.compoundsList.getSelected()
        if not selected:
            wx.Bell()
            return

        index = self.compoundsList.GetItemData(selected[0])
        # formula = self.currentCompounds[index][4]
        formula = self.currentCompounds[index].formula

        # make text object for data
        obj = wx.TextDataObject()
        obj.SetText(formula)
        
        # paste to clipboard
        if wx.TheClipboard.Open():
            wx.TheClipboard.SetData(obj)
            wx.TheClipboard.Close()
    # ----
    
    
    def onListKey(self, evt):
        """Export list if Ctrl+C."""
        
        # get key
        key = evt.GetKeyCode()
        
        # copy
        if key == 67 and evt.CmdDown():
            self.onListCopy()
            
        # other keys
        else:
            evt.Skip()
    # ----
    
    
    def onListRMU(self, evt):
        """Show filter pop-up menu on lists."""
        
        # popup menu
        menu = wx.Menu()
        menu.Append(ID_listViewAll, "Show All", "", wx.ITEM_RADIO)
        menu.Append(ID_listViewMatched, "Show Matched Only", "", wx.ITEM_RADIO)
        menu.Append(ID_listViewUnmatched, "Show Unmatched Only", "", wx.ITEM_RADIO)
        menu.AppendSeparator()
        menu.Append(ID_listSendToMassCalculator, "Show Isotopic Pattern", "")
        menu.AppendSeparator()
        menu.Append(ID_listCopyFormula, "Copy Formula")
        menu.Append(ID_listCopy, "Copy List")
        
        # check item
        if self._compoundsFilter == 1:
            menu.Check(ID_listViewMatched, True)
        elif self._compoundsFilter == -1:
            menu.Check(ID_listViewUnmatched, True)
        else:
            menu.Check(ID_listViewAll, True)
        
        # bind events
        self.Bind(wx.EVT_MENU, self.onListFilter, id=ID_listViewAll)
        self.Bind(wx.EVT_MENU, self.onListFilter, id=ID_listViewMatched)
        self.Bind(wx.EVT_MENU, self.onListFilter, id=ID_listViewUnmatched)
        self.Bind(wx.EVT_MENU, self.onItemSendToMassCalculator, id=ID_listSendToMassCalculator)
        self.Bind(wx.EVT_MENU, self.onItemCopyFormula, id=ID_listCopyFormula)
        self.Bind(wx.EVT_MENU, self.onListCopy, id=ID_listCopy)
        
        # show menu
        self.PopupMenu(menu)
        menu.Destroy()
        self.SetFocus()
    # ----
    
    
    def onListFilter(self, evt):
        """Apply selected view filter on current list."""
        
        # set filter
        if evt.GetId() == ID_listViewMatched:
            self._compoundsFilter = 1
        elif evt.GetId() == ID_listViewUnmatched:
            self._compoundsFilter = -1
        else:
            self._compoundsFilter = 0
        
        # update list
        self.updateCompoundsList()
    # ----
    
    
    def onListCopy(self, evt=None):
        """Copy items into clipboard."""
        self.compoundsList.copyToClipboard()
    # ----
    
    
    def onGenerate(self, evt=None):
        """Generate compounds ions."""
        
        # check processing
        if self.processing:
            return
        
        # clear recent
        self.currentCompounds = []
        compounds = {}
        
        # clear match panel
        if self.matchPanel:
            self.matchPanel.clear()
        
        # get params
        if not self.getParams():
            self.updateCompoundsList()
            return
        
        # get compounds from selected group or formula
        if self.currentTool == 'compounds':
            group = self.compounds_choice.GetStringSelection()
            if group and group in libs.compounds:
                compounds = libs.compounds[group]
        else:
            formula = self.formula_value.GetValue()
            if formula:
                try:
                    compounds[formula] = mspy.compound(formula)
                except:
                    wx.Bell()
        
        # check compounds
        if not compounds:
            self.updateCompoundsList()
            return
        
        # show processing gauge
        self.onProcessing(True)
        self.generate_butt.Enable(False)
        self.match_butt.Enable(False)
        self.annotate_butt.Enable(False)
        
        # do processing
        self.processing = threading.Thread(target=self.runGenerateIons, kwargs={'compounds':compounds})
        self.processing.start()
        
        # pulse gauge while working
        while self.processing and self.processing.isAlive():
            self.gauge.pulse()
        
        # update compounds list
        self._compoundsFilter = 0
        self.updateCompoundsList()
        
        # hide processing gauge
        self.onProcessing(False)
        self.generate_butt.Enable(True)
        self.match_butt.Enable(True)
        self.annotate_butt.Enable(True)

        # send data to match panel
        if self.matchPanel:
            # $$ 22.04
            self.setMatchPanelData()
    # ----
    
    
    def onMatch(self, evt=None):
        """Match data to current peaklist."""
        
        # init match panel
        match = True
        if not self.matchPanel:
            match = False
            self.matchPanel = panelMatch(self, self.parent, 'compounds')
            self.matchPanel.Centre()
            self.matchPanel.Show(True)
        
        # set data
        # $$ 22.04
        self.setMatchPanelData()
        
        # raise panel
        if evt:
            self.matchPanel.Raise()
        
        # match data
        if match and evt:
            self.matchPanel.onMatch()
    # ----
    
    
    def onAnnotate(self, evt):
        """Annotate matched peaks."""
        
        # check document
        if self.currentDocument == None:
            wx.Bell()
            return
        
        # check compounds
        if len(self.currentCompounds) == 0:
            wx.Bell()
            return
        
        # get annotations
        annotations = []
        for item in self.currentCompounds:
            # $$ 22.04, just a fix for possible errors
            if item.matches == None:
                continue
            for annotation in item.matches:
                annotation.label = item.name
                if item.adduct == 'radical':
                    annotation.label += ' (radical)'
                    annotation.radical = 1
                elif item.adduct:
                    annotation.label += ' (%s)' % item.adduct
                annotation.charge = item.z
                annotation.formula = item.formula
                annotations.append(annotation)
        
        # store annotation
        self.currentDocument.backup(('annotations'))
        self.currentDocument.annotations += annotations
        self.currentDocument.sortAnnotations()
        self.parent.onDocumentChanged(items=('annotations'))
    # ----
    
    
    def setData(self, document):
        """Set current document."""
        
        # set new document
        self.currentDocument = document
        
        # clear previous matches
        self.clearMatches()
    # ----
    
    
    def getParams(self):
        """Get generate params."""
        
        # try to get values
        try:
            config.compoundsSearch['massType'] = 0
            if self.massTypeAv_radio.GetValue():
                config.compoundsSearch['massType'] = 1
            
            config.compoundsSearch['maxCharge'] = int(self.maxCharge_value.GetValue())
            config.compoundsSearch['radicals'] = int(self.radicals_check.GetValue())
            
            config.compoundsSearch['adducts'] = []
            config.compoundsSearch['isotopes'] = []

            
            if self.adductM_H2O_H_minus_check.GetValue():
                config.compoundsSearch['adducts'].append('[M-H2O-H]-')
            if self.adductM_H2O_H_plus_check.GetValue():
                config.compoundsSearch['adducts'].append('[M-H2O+H]+')
            if self.adductACN_check.GetValue():
                config.compoundsSearch['adducts'].append('[+ACN+H]+')
            if self.adductMeOH_check.GetValue():
                config.compoundsSearch['adducts'].append('[+MeOH+H]+')

            #fm edited
            if self.adduct13C1_check.GetValue():
                config.compoundsSearch['isotopes'].append('(13)C1')
            if self.adduct13C2_check.GetValue():
                config.compoundsSearch['isotopes'].append('(13)C2')
            if self.adduct13C3_check.GetValue():
                config.compoundsSearch['isotopes'].append('(13)C3')
            if self.adduct13C4_check.GetValue():
                config.compoundsSearch['isotopes'].append('(13)C4')
            if self.adduct13C5_check.GetValue():
                config.compoundsSearch['isotopes'].append('(13)C5')
            if self.adduct13C6_check.GetValue():
                config.compoundsSearch['isotopes'].append('(13)C6')
            if self.adduct15N1_check.GetValue():
                config.compoundsSearch['isotopes'].append('(15)N1')
            if self.adduct15N2_check.GetValue():
                config.compoundsSearch['isotopes'].append('(15)N2')
            if self.adduct15N3_check.GetValue():
                config.compoundsSearch['isotopes'].append('(15)N3')
            if self.adduct15N4_check.GetValue():
                config.compoundsSearch['isotopes'].append('(15)N4')
            if self.adduct15N5_check.GetValue():
                config.compoundsSearch['isotopes'].append('(15)N5')
            if self.adduct15N6_check.GetValue():
                config.compoundsSearch['isotopes'].append('(15)N6')
            if self.adduct15N7_check.GetValue():
                config.compoundsSearch['isotopes'].append('(15)N7')
            if self.adduct15N8_check.GetValue():
                config.compoundsSearch['isotopes'].append('(15)N8')
            if self.adduct15N9_check.GetValue():
                config.compoundsSearch['isotopes'].append('(15)N9')
            if self.adductM_Cl_check.GetValue():
                config.compoundsSearch['adducts'].append('[M+Cl]-')
            if self.adductM_NA_2H_check.GetValue():
                config.compoundsSearch['adducts'].append('[M+Na-2H]-')
            if self.adductM_K_2H_check.GetValue():
                config.compoundsSearch['adducts'].append('[M+K-2H]-')
            if self.adduct_M_CH3_check.GetValue():
                config.compoundsSearch['adducts'].append('[M-CH3]-')
            if self.adduct_M_C3H10N_check.GetValue():
                config.compoundsSearch['adducts'].append('[M-C3H10N]-')
            if self.adduct_M_C5H12N_check.GetValue():
                config.compoundsSearch['adducts'].append('[M-C5H12N]-')
            if self.adduct_M_Na_check.GetValue():
                config.compoundsSearch['adducts'].append('[M+Na]+')
            if self.adduct_M_K_check.GetValue():
                config.compoundsSearch['adducts'].append('[M+K]+')
            if self.adductLi_check.GetValue():
                config.compoundsSearch['adducts'].append('[M+Li]+')
            if self.adduct_M_NH4_check.GetValue():
                config.compoundsSearch['adducts'].append('[M+NH4]+')
            if self.adduct_M2_H_check.GetValue():
                config.compoundsSearch['adducts'].append('[2M+H]+')
            if self.adduct_M2_Na_check.GetValue():
                config.compoundsSearch['adducts'].append('[2M+Na]+')
            if self.adduct_M2_K_check.GetValue():
                config.compoundsSearch['adducts'].append('[2M+K]+')
            if self.adduct_M2_NH4_check.GetValue():
                config.compoundsSearch['adducts'].append('[2M+NH4]+')
            if self.adduct_M2_NEG_H_check.GetValue():
                config.compoundsSearch['adducts'].append('[2M-H]-')
            if self.adduct_M2_Cl_check.GetValue():
                config.compoundsSearch['adducts'].append('[2M+Cl]-')
            if self.adduct_M2_Na_2H_check.GetValue():
                config.compoundsSearch['adducts'].append('[2M+Na-2H]-')
            if self.adduct_M2_K_2H_check.GetValue():
                config.compoundsSearch['adducts'].append('[2M+K-2H]-')
            if self.adduct_FMP10_check.GetValue():
                config.compoundsSearch['adducts'].append('[M+FMP10]+')
            if self.adduct_2FMP10_check.GetValue():
                config.compoundsSearch['adducts'].append('[M+2FMP10]+')
            if self.adduct_2FMP10_CH3_check.GetValue():
                config.compoundsSearch['adducts'].append('[M+2FMP10-CH3]+')
            if self.adduct_AMPP_check.GetValue():
                config.compoundsSearch['adducts'].append('[M+AMPP]+')
            if self.adduct_2AMPP_check.GetValue():
                config.compoundsSearch['adducts'].append('[M+2AMPP]+')
            if self.adduct_3AMPP_check.GetValue():
                config.compoundsSearch['adducts'].append('[M+3AMPP]+')
            #fm edited end
            return True
        except:
            wx.Bell()
            return False
    # ----
    
    
    def updateCompoundsList(self):
        """Update compounds mass list."""
        
        # clear previous data and set new
        self.compoundsList.DeleteAllItems()
        listStyleCompounds = []
        for c in self.currentCompounds:
            # $$ 21.04
            # must follow the same order as the table columns
            # "Compound", "Adduct", "Isotope", "Formula", "m/z database", "m/z measured", "Error (ppm)", "z"
            listStyleCompounds.append([c.name, c.adduct, c.isotope, c.formula, c.mz, c.measuredMz, c.error, c.z])
        self.compoundsList.setDataMap(listStyleCompounds)

        # check data
        if len(self.currentCompounds) == 0:
            return
        
        # add new data
        mzFormat = '%0.' + `config.main['mzDigits']` + 'f'
        #$$ 2 des.m.
        errFormat = "%.2f"  
        if config.match['units'] == 'ppm':
            errFormat = "%.2f"
        fontMatched = wx.Font(mwx.SMALL_FONT_SIZE, wx.FONTFAMILY_DEFAULT, wx.FONTSTYLE_NORMAL, wx.FONTWEIGHT_BOLD)
        
        row = -1
        for index, item in enumerate(self.currentCompounds):
            # filter data
            if self._compoundsFilter == 1 and item.error == None:
                continue
            elif self._compoundsFilter == -1 and item.error != None:
                continue
            
            mz = ''
            z = ''
            adduct = ''
            formula = ''
            error = ''
            measured = ''
            isotope = ''
            if item.mz != None:
                mz = mzFormat % (item.mz)
            if item.z != None:
                z = str(item.z)
            if item.adduct != None:
                adduct = item.adduct
            if item.isotope != None:
                isotope = item.isotope
            if item.formula != None:
                formula = item.formula
            if item.error != None:
                error = errFormat % (item.error)
            if item.measuredMz != None:
                measured = mzFormat % (item.measuredMz)
            
            
            # add data
            row += 1
            self.compoundsList.InsertStringItem(row, '')
            self.compoundsList.SetStringItem(row, 0, item.name)
            self.compoundsList.SetStringItem(row, 1, adduct)
            self.compoundsList.SetStringItem(row, 2, isotope)
            self.compoundsList.SetStringItem(row, 3, formula)
            self.compoundsList.SetStringItem(row, 4, mz)
            self.compoundsList.SetStringItem(row, 5, measured)
            self.compoundsList.SetStringItem(row, 6, error)
            self.compoundsList.SetStringItem(row, 7, z)
            self.compoundsList.SetItemData(row, index)

            # mark matched
            if item.error != None:
                self.compoundsList.SetItemTextColour(row, (0,200,0))
                self.compoundsList.SetItemFont(row, fontMatched)
        
        # sort data
        self.compoundsList.sort()
        
        # scroll top
        if self.compoundsList.GetItemCount():
            self.compoundsList.EnsureVisible(0)
    # ----
    
    
    def updateMatches(self, resultList=None):
        """Update compounds list."""
        # $$ 21.04, 22.04
        # take data from panelMatch and update current compounds
        matchedCompounds = []
        for mc in self.matchPanel.currentData:
            # 0 name, 1 m/z, 2 z, 3 adduct, 4 formula, 5 error, 6 matches, 7 measured m/z, 8 isotope
            matchedCompounds.append(CurrentCompound(name=mc[0], mz=mc[1], z=mc[2], adduct=mc[3], formula=mc[4], error=mc[5], matches=mc[6], measuredMz=mc[7], isotope=mc[8]))
        self.currentCompounds = matchedCompounds

        # update compounds list
        self.updateCompoundsList()
    # ----
    
    
    def clearMatches(self):
        """Clear matched data."""
        
        # update compounds panel
        if len(self.currentCompounds) != 0:
            for item in self.currentCompounds:
                item.error = None
                item.matches = []
                item.measuredMz = None
            self.updateCompoundsList()
        
        # clear match panel
        if self.matchPanel:
            # $$ 22.04
            self.setMatchPanelData()
    # ----
    
    
    def runGenerateIons(self, compounds):
        """Calculate compounds ions."""
        # run task
        try:
            # get max charge and polarity
            polarity = -1 if config.compoundsSearch['maxCharge'] < 0 else 1
            maxCharge = abs(config.compoundsSearch['maxCharge']) + 1
            defaultAdduct = '[M-H]-' if polarity < 0 else '[M+H]+'
            adducts = config.compoundsSearch['adducts'][:]
            adducts.append(defaultAdduct) # always combine with the main ion

            # generate compounds ions
            self.currentCompounds = []
            for name, compound in sorted(compounds.items()):
                # check compound
                if not compound.isvalid():
                    continue
                
                # walk in charges
                for z in range(1, maxCharge):
                    mspy.CHECK_FORCE_QUIT()

                    # main ion
                    #adduct = '[M-H]-' if polarity < 0 else '[M+H]+'
                    #mz = compound.mz(z*polarity, agentCharge=1)[config.compoundsSearch['massType']]
                    #self.currentCompounds.append(CurrentCompound(name=name, mz=mz, z=z*polarity, adduct=adduct, formula=compound.expression))                    
                    
                    # radicals
                    if config.compoundsSearch['radicals']:
                        mz = compound.mz(z*polarity, agentFormula='e', agentCharge=-1)[config.compoundsSearch['massType']]
                        self.currentCompounds.append(CurrentCompound(name=name, mz=mz, z=z*polarity, adduct='M*', formula=compound.expression))

                    # add adducts
                    for adduct in adducts:
                        mspy.CHECK_FORCE_QUIT()
                        adductFormula = FORMULAS[adduct]

                        if adduct in ('[M+Li]+', '[M+Na-2H]-', '[M+K-2H]-', '[M+Na]+', '[M+K]+', '[M+NH4]+'):
                            formula = '%s(%s)(H-1)' % (compound.expression, adductFormula)
                        elif adduct in ('[M+Cl]-', '[M-CH3]-', '[M-C3H10N]-', '[M-C5H12N]-'):
                            formula = '%s(%s)(H)' % (compound.expression, adductFormula)
                        elif adduct in ('[2M+Na]+', '[2M+K]+', '[2M+NH4]+', '[2M+H]+', '[2M-H]-'): # TODO check formulas [2M-H]-
                            formula = '%s(%s)(H-1)' % (2*compound.expression, adductFormula)
                        elif adduct in ('[2M+Cl]-', '[2M+Na-2H]-', '[2M+K-2H]-'):
                            formula = '%s(%s)(H)' % (2*compound.expression, adductFormula)
                        elif adduct in ('[M-H2O-H]-', '[M-H2O+H]+', '[+MeOH+H]+', '[+ACN+H]+', '[M+FMP10]+', '[M+2FMP10]+', '[M+2FMP10-CH3]+', '[M+AMPP]+', '[M+2AMPP]+', '[M+3AMPP]+'):
                            formula = '%s(%s)' % (compound.expression, adductFormula)
                        else:
                            # default adduct or something that was not yet defined
                            formula = '%s' % (compound.expression)

                        adductCompound = mspy.compound(formula)
                        print('Adduct combination compound: %s, valid: %s' % (formula, adductCompound.isvalid()))
                        if not adductCompound.isvalid():
                            continue

                        mz = adductCompound.mz(z*polarity)[config.compoundsSearch['massType']]
                        self.currentCompounds.append(CurrentCompound(
                            name=name, mz=mz, z=z*polarity, adduct=adduct, formula=adductCompound.expression))

                        # find single isotope combinations
                        for iso in ('(13)C1', '(13)C2', '(13)C3', '(13)C4', '(13)C5', '(13)C6', '(15)N1', '(15)N2', '(15)N3', '(15)N4', '(15)N5', '(15)N6', '(15)N7', '(15)N8', '(15)N9'):
                            if iso not in config.compoundsSearch['isotopes']:
                                continue

                            combinationFormula = '%s(%s)' % (formula, FORMULAS[iso])
                            combinationCompound = mspy.compound(combinationFormula)

                            print('1-Isotope combination: %s, valid: %s' % (combinationFormula, combinationCompound.isvalid()))
                            if not combinationCompound.isvalid():
                                continue

                            mz = combinationCompound.mz(z*polarity)[config.compoundsSearch['massType']]
                            self.currentCompounds.append(CurrentCompound(
                                name=name, mz=mz, z=z*polarity, adduct=adduct, isotope=iso, formula=combinationCompound.expression))

                        # find double isotope combinations
                        for iso1 in ('(13)C1', '(13)C2', '(13)C3', '(13)C4', '(13)C5', '(13)C6'):
                            if iso1 not in config.compoundsSearch['isotopes']:
                                continue
                            for iso2 in ('(15)N1', '(15)N2', '(15)N3', '(15)N4', '(15)N5', '(15)N6', '(15)N7', '(15)N8', '(15)N9'):
                                if iso2 not in config.compoundsSearch['isotopes']:
                                    continue

                                combinationFormula = '%s(%s)(%s)' % (formula, FORMULAS[iso1], FORMULAS[iso2])
                                combinationCompound = mspy.compound(combinationFormula)

                                print('2-Isotope combination: %s, valid: %s' % (combinationFormula, combinationCompound.isvalid()))
                                if not combinationCompound.isvalid():
                                    continue

                                isoCombination = '%s%s' % (iso1, iso2)
                                mz = combinationCompound.mz(z*polarity)[config.compoundsSearch['massType']]
                                self.currentCompounds.append(CurrentCompound(
                                    name=name, mz=mz, z=z*polarity, adduct=adduct, isotope=isoCombination, formula=combinationCompound.expression))



                    # $$ rewritten combination logic
                    # first one is empty to make 2-isotopes combinations with the default adduct
                    # TODO: original code supported adduct combinations like `Li - +MeOH+H` -- is it necessary?
                    # for adduct in ('', '[M+Li]+', '[M+Na-2H]-', '[M+K-2H]-', '[M+Na]+', '[M+K]+'): # taken from the original code, might be necessary to add more adducts
                    #     if adduct != '' and not adduct in config.compoundsSearch['adducts']:
                    #         continue

                    #     # don't make single isotope combinations for the default adduct as they've already been added in the previous steps
                    #     if adduct != '':
                    #         for iso in ('(13)C1', '(13)C2', '(13)C3', '(13)C4', '(13)C5', '(13)C6', '(15)N1', '(15)N2', '(15)N3', '(15)N4', '(15)N5', '(15)N6', '(15)N7', '(15)N8', '(15)N9'):
                    #             if not iso in config.compoundsSearch['isotopes']:
                    #                 continue

                    #             formula = '%s(%s)(H-1)(%s)' % (compound.expression, FORMULAS[adduct], FORMULAS[iso])
                    #             formula = mspy.compound(formula)

                    #             if formula.isvalid():
                    #                 mz = formula.mz(z*polarity)[config.compoundsSearch['massType']]
                    #                 self.currentCompounds.append(CurrentCompound(name=name, mz=mz, z=z*polarity, adduct=adduct, isotope=iso, formula=formula.expression))

                    # for adduct in ('', '[M+Cl]-'): # taken from the original code, might be necessary to add more adducts
                    #     if adduct != '' and not adduct in config.compoundsSearch['adducts']:
                    #         continue

                    #     # don't make single isotope combinations for the default adduct as they've already been added in the previous steps
                    #     if adduct != '':
                    #         for iso in ('(13)C1', '(13)C2', '(13)C3', '(13)C4', '(13)C5', '(13)C6', '(15)N1', '(15)N2', '(15)N3', '(15)N4', '(15)N5', '(15)N6', '(15)N7', '(15)N8', '(15)N9'):
                    #             if not iso in config.compoundsSearch['isotopes']:
                    #                 continue

                    #             formula = '%s(%s)(H)(%s)' % (compound.expression, FORMULAS[adduct], FORMULAS[iso])
                    #             formula = mspy.compound(formula)

                    #             if formula.isvalid():
                    #                 mz = formula.mz(z*polarity)[config.compoundsSearch['massType']]
                    #                 self.currentCompounds.append(CurrentCompound(name=name, mz=mz, z=z*polarity, adduct=adduct, isotope=iso, formula=formula.expression))

                    #     for is1 in ('(13)C1', '(13)C2', '(13)C3', '(13)C4', '(13)C5', '(13)C6'):
                    #         if not is1 in config.compoundsSearch['isotopes']:
                    #             continue
                    #         for is2 in ('(15)N1', '(15)N2', '(15)N3', '(15)N4', '(15)N5', '(15)N6', '(15)N7', '(15)N8', '(15)N9'):
                    #             if not is2 in config.compoundsSearch['isotopes']:
                    #                 continue

                    #             isCombination = '%s%s' % (is1, is2)
                    #             if adduct != '':
                    #                 if adduct == '[M+Cl]-':
                    #                     resAdduct = adduct
                    #                     formula = '%s(%s)(H)(%s)(%s)' % (compound.expression, FORMULAS[adduct], FORMULAS[is1], FORMULAS[is2])
                    #                 else:
                    #                    resAdduct = adduct 
                    #                    formula = '%s(%s)(H-1)(%s)(%s)' % (compound.expression, FORMULAS[adduct], FORMULAS[is1], FORMULAS[is2])
                                
                    #             elif polarity < 0 : 
                    #                 resAdduct = '[M-H]-' if polarity < 0 else '[M+H]+'
                    #                 formula = '%s(%s)(%s)' % (compound.expression, FORMULAS[is1], FORMULAS[is2])

                                
                    #             formula = mspy.compound(formula)
                    #             if formula.isvalid():
                    #                 mz = formula.mz(z*polarity)[config.compoundsSearch['massType']]
                    #                 self.currentCompounds.append(CurrentCompound(name=name, mz=mz, z=z*polarity, adduct=resAdduct, isotope=isCombination, formula=formula.expression))

                    # $$ old logic, left here for the reference
                    # add combinations
                    # for item1 in ('Li', '(13)C1', '(13)C2', '(13)C3', '(13)C4', '(13)C5', '(13)C6', '(13)C7', '(13)C8', '(13)C9', '(13)C10', '[M+Cl]-', '[M+Na-2H]-', '[M+K-2H]-', '[M+Na]+', '[M+K]+'):
                    #     if item1 in common:
                    #         for item2 in ('+ACN+H', '+MeOH+H', '-H2O', '(15)N1', '(15)N2', '(15)N3', '(15)N4', '(15)N5', '(15)N6', '(15)N7', '(15)N8', '(15)N9'):
                    #             if item2 in common:
                                    
                    #                 if item2 in ('+ACN+H', '+MeOH+H', '(15)N1', '(15)N2', '(15)N3', '(15)N4', '(15)N5', '(15)N6',  '(15)N7', '(15)N8', '(15)N9'):
                    #                     adduct = '%s%s' % (item1, item2)
                    #                     formula = '%s(%s)(%s)' % (compound.expression, FORMULAS[item1], FORMULAS[item2])
                    #                 elif item2 in ('-H2O'):
                    #                     adduct = '%s%s' % (item1, item2)
                    #                     formula = '%s(%s)(%s)(H-1)' % (compound.expression, FORMULAS[item1], FORMULAS[item2])
                                    
                    #                 formula = mspy.compound(formula)
                    #                 if formula.isvalid():
                    #                     mz = formula.mz(z*polarity)[config.compoundsSearch['massType']]
                    #                     self.currentCompounds.append(CurrentCompound(name=name, mz=mz, z=z*polarity, adduct=adduct, formula=formula.expression))
        
        # task canceled
        except mspy.ForceQuit:
            self.currentCompounds = []
            return
    # ----
    
    
    def calibrateByMatches(self, references):
        """Use matches for calibration."""
        self.parent.onToolsCalibration(references=references)

    def setMatchPanelData(self):
        # $$ 22.04, separate function because this logic is used often
        matchStyleCompounds = []
        for c in self.currentCompounds:
            # 0 name, 1 m/z, 2 z, 3 adduct, 4 formula, 5 error, 6 matches, 7 measured m/z, 8 isotope
            matchStyleCompounds.append([c.name, c.mz, c.z, c.adduct, c.formula, c.error, c.matches, c.measuredMz, c.isotope])

        self.matchPanel.setData(matchStyleCompounds)
    # ----
    
    
