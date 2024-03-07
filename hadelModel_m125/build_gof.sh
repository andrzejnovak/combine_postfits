combineCards.py failhadel2016APV=failhadel2016APV.txt topCRfailhadel2016APV=topCRfailhadel2016APV.txt wlnuCRfailhadel2016APV=wlnuCRfailhadel2016APV.txt loosepasshadel2016APV=loosepasshadel2016APV.txt topCRloosepasshadel2016APV=topCRloosepasshadel2016APV.txt wlnuCRloosepasshadel2016APV=wlnuCRloosepasshadel2016APV.txt passhadel2016APV=passhadel2016APV.txt topCRpasshadel2016APV=topCRpasshadel2016APV.txt wlnuCRpasshadel2016APV=wlnuCRpasshadel2016APV.txt > hadelModel_combined.txt
text2workspace.py hadelModel_combined.txt --channel-masks
combine -M GoodnessOfFit -d hadelModel_combined.root -m 125 --algo=saturated -n _result_bonly_CRonly --setParametersForFit mask_passhadel2016APV=1 --setParametersForEval mask_passhadel2016APV=0 --freezeParameters r --setParameters r=0,mask_passhadel2016APV=1 -t 500 --toysFrequentist
combine -M GoodnessOfFit -d hadelModel_combined.root -m 125 --algo=saturated -n _result_bonly_CRonly_data --setParametersForFit mask_passhadel2016APV=1 --setParametersForEval mask_passhadel2016APV=0 --freezeParameters r --setParameters r=0,mask_passhadel2016APV=1
combine -M GoodnessOfFit -d hadelModel_combined.root -m 125 --algo=saturated -n _result_sb -t 500 --toysFrequentist
combine -M GoodnessOfFit -d hadelModel_combined.root -m 125 --algo=saturated -n _result_sb_data
combineTool.py -M CollectGoodnessOfFit --input higgsCombine_result_bonly_CRonly_data.GoodnessOfFit.mH125.root higgsCombine_result_bonly_CRonly.GoodnessOfFit.mH125.123456.root -m 125 -o gof_CRonly.json
combineTool.py -M CollectGoodnessOfFit --input higgsCombine_result_sb_data.GoodnessOfFit.mH125.root higgsCombine_result_sb.GoodnessOfFit.mH125.123456.root -m 125 -o gof.json
plotGof.py gof_CRonly.json --statistic saturated --mass 125.0 -o gof_plot_CRonly --title-right=hadelModel_2016APV_CRonly
plotGof.py gof.json --statistic saturated --mass 125.0 -o gof_plot --title-right=hadelModel_2016APV
