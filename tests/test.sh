P=0
DPI=100
OPTS="--noroot"

if [ "$1" = "A" ] || [ "$1" = "all" ]; then
    combine_postfits --dpi $DPI -i fitDiags/fit_diag_A.root -o outs/plots_A_all --data --unblind  -p $P   $OP  
    combine_postfits --dpi $DPI -i fitDiags/fit_diag_A.root -o outs/plots_A --style styles/style_A.yml --data --unblind --sigs hcc,zcc --onto qcd --rmap zcc:z,hcc:r  --cats 'pass:ptbin*pass2016;fail:ptbin*fail*;muCRpass:muonCRpass2016;muCRfail:muonCRfail2016' --bkgs top,other,wqq,wcq,zqq,zbb,hbb   --project-signal 200,0 -p $P   $OP
fi

if [ "$1" = "Abig" ] || [ "$1" = "all" ]; then
    combine_postfits --dpi $DPI -i fitDiags/fit_diag_Abig.root -o outs/plots_Abig_all --data --unblind  -p $P   $OP  
    combine_postfits --dpi $DPI -i fitDiags/fit_diag_Abig.root -o outs/plots_Abig --style styles/style_A.yml --data --unblind --sigs hcc,zcc --onto qcd --rmap zcc:z,hcc:r  --cats 'pass16:ptbin*pass2016;fail16:ptbin*fail2016;pass17:ptbin*pass2017;fail17:ptbin*fail2017;pass18:ptbin*pass2018;fail18:ptbin*fail2018;pass:ptbin*pass*;fail:ptbin*fail*;muCRpass16:muonCRpass2016;muCRfail16:muonCRfail2016;muCRpass17:muonCRpass2017;muCRfail17:muonCRfail2017;muCRpass18:muonCRpass2018;muCRfail18:muonCRfail2018' --bkgs top,other,wqq,wcq,zqq,zbb,hbb   --project-signal 200,0 -p $P   $OP
fi

if [ "$1" = "B" ] || [ "$1" = "all" ]; then
    combine_postfits --dpi $DPI -i fitDiags/fit_diag_B.root -o outs/plots_B_all --MC  -p $P   $OP  
    combine_postfits --dpi $DPI -i fitDiags/fit_diag_B.root --data --unblind -o outs/plots_B --style styles/style_B.yml  --xlabel 'Jet $m_{SD}$' --sigs b150,m150 --project-signals 2,2 --rmap 'm150:r_q,b150:r_b' --bkgs top,vlep,wqq,zqq,zbb,hbb --onto 2017_qcd --cats 'fail:ptbin*fail;passlow:ptbin*high*;passhigh:ptbin*passlow*'   -p $P   $OP
fi

if [ "$1" = "C" ] || [ "$1" = "all" ]; then
    combine_postfits --dpi $DPI -i fitDiags/fit_diag_C.root -o outs/plots_C_all --MC    -p $P   $OP
    combine_postfits --dpi $DPI -i fitDiags/fit_diag_C.root -o outs/plots_C --toys  --style styles/style_C.yml --xlabel 'Jet $m_{reg}$'   $OP
fi

if [ "$1" = "D" ] || [ "$1" = "all" ]; then
    combine_postfits --dpi $DPI -i fitDiags/fit_diag_D.root -o outs/plots_D_all --MC   -p $P   $OP
    combine_postfits --dpi $DPI -i fitDiags/fit_diag_D.root -o outs/plots_D --MC --style styles/style_D.yml --onto qcd --sigs VH --bkgs qcd,top,Wjets,Zjets,VV,H  --rmap 'VH:rVH' --project-signals 3 --xlabel 'Jet $m_{SD}$' -p $P   $OP --vv
fi
