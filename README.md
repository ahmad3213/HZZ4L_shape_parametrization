#HZZ4L Signal Shape Parametrization


##Usage

1. make sure to have ROOT environment, but also the HiggsCombination package in your CMSSW area (needed for RooDoubleCB).


2. Check the options and what they are used for. Normally, I run it like:

    python m4l_simultaneous_spectrum_fitter_for_DCB_params_v2.py --dir=/tree/directory/ --obsName=mass4l --obsBins="|105.0|140.0|" -l -q -b --doFit -s 4e,4mu,2e2mu,2mu2e,2e2mu_inclusive


3. Add **--doDatasets** first time to produce a workspace with datasets, so that you
    dont have to do it again and again - takes a lot of time.
4. To do closure test and measure the ch-square, i.e. to fit with parameterization written in e.g DCB_parametrization.yaml and legacy_DCB_parametrization.yaml
    add to 2.:

    --doClosure --closureParams DCB_parametrization.yaml,legacy_DCB_parametrization.yaml
