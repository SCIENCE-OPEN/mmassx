function status = matlab_launch_mmass(doc_to_open)
if nargin<1, doc_to_open = ''; end
path_ana   = 'C:\Users\YellenGary\anaconda3';
path_mmass = 'D:\Documents\mMass_repo';
command_py = ['call "' path_ana '\scripts\activate.bat" base & ' ...
    path_mmass(1:2) '& cd "' path_mmass '" & python mmass.py '];
% doc_to_open = '"N:\YELLEN LAB\MSI\13C lactate\20220217_13Clactate_N1-3_mMass\N1_35minCtrl_DG-OverviewSpectra.csv"';

% note that this command will return before mMass is closed, but a command
% window will open and remain open
status = system([command_py doc_to_open ' &']);
