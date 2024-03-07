combineCards.py failhadel2016APV=failhadel2016APV.txt topCRfailhadel2016APV=topCRfailhadel2016APV.txt wlnuCRfailhadel2016APV=wlnuCRfailhadel2016APV.txt loosepasshadel2016APV=loosepasshadel2016APV.txt topCRloosepasshadel2016APV=topCRloosepasshadel2016APV.txt wlnuCRloosepasshadel2016APV=wlnuCRloosepasshadel2016APV.txt passhadel2016APV=passhadel2016APV.txt topCRpasshadel2016APV=topCRpasshadel2016APV.txt wlnuCRpasshadel2016APV=wlnuCRpasshadel2016APV.txt > hadelModel_combined.txt
text2workspace.py hadelModel_combined.txt
combine -M AsymptoticLimits hadelModel_combined.root -m 125 --rMin -200 --rMax 1000 --expectSignal 0 -n .hadelModel -v 3 -t -1
combine -M FitDiagnostics hadelModel_combined.root -m 125 --rMin -200 --rMax 1000 --expectSignal 0 --saveShapes --saveWithUncertainties -n .hadelModel -v 3 -t -1
combineTool.py -M Impacts -d hadelModel_combined.root -m 125 --rMin -200 --rMax 1000 --robustFit 1 --doInitialFit --expectSignal 0 -t -1
combineTool.py -M Impacts -d hadelModel_combined.root -m 125 --rMin -200 --rMax 1000 --robustFit 1 --doFits --expectSignal 0 -t -1
combineTool.py -M Impacts -d hadelModel_combined.root -m 125 --rMin -200 --rMax 1000 --robustFit 1 --output impacts_m125.json --expectSignal 0 -t -1
plotImpacts.py -i impacts_m125.json -o impacts_hadelModel
