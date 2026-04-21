# References — FreeEEG128 hardware design

Curated references for evolving the NeuroIDSS FreeEEG128-alpha into a beta
revision. Focus: EEG acquisition-system design, validation, and benchmarking
(not signal-processing methods).

> ⚠️ **Live-access caveat**: the research agent that compiled refs 1-25 had
> `paperclip` MCP access but **no WebSearch / WebFetch** — refs 26-37 are
> drawn from standard bibliographic knowledge (cutoff Jan 2026) and should
> be spot-checked before citation. Ref [38] (Black 2017) is **unverified**
> — see §Priority-1 below.

---

## Priority 1 — Black et al. 2017: RESOLVED

Full citation:

> **Black, C., Voigts, J., Agrawal, U., Ladow, M., Santoyo, J., Moore, C. & Jones, S.** "Open Ephys electroencephalography (Open Ephys + EEG): a modular, low-cost, open-source solution to human neural recording." *Journal of Neural Engineering* **14**(3), 035002 (2017). DOI: [10.1088/1741-2552/aa651f](https://doi.org/10.1088/1741-2552/aa651f).

This is the **primary comparison benchmark** for the FreeEEG128 beta design.
Full feature matrix vs. FreeEEG128 lives in `COMPARISON.md §Black 2017 vs FreeEEG128`.

Abstract quote:

> "The Open Ephys + EEG system can record reliable human EEG data, as well as human EMG data. A side-by-side comparison of eyes closed 8-14 Hz activity between the Open Ephys + EEG system and the Brainvision ActiCHamp EEG system showed similar average power and signal to noise."

Comparison paradigm is **resting-state alpha (eyes-closed 8-14 Hz)**, not
SSVEP or ERP — useful to know for our own validation study (we should
reproduce this exact benchmark).

---

## Historical foundations

The FreeEEG128 design inherits from four decades of high-density EEG work.
See `HISTORY.md` for the full lineage.

- Nunez's biophysical treatment of scalp potentials [A1, A2] grounds the
  electrode-count and reference-scheme arguments. The surface-Laplacian /
  high-resolution EEG debate [A3] motivated the 64→128→256 channel race.
- Gevins' engineering program at EEG Systems Laboratory / SAM Technology
  produced "deblurring" methods and real-time cognitive-state EEG [A4];
  see also <https://www.eeg.com/alan_gevins.php>.
- The **first 256-channel EEG system** was built at Neuroscan by M.E. Pflieger and S.F. Sands (principals), documented in Pflieger & Sands 1996 [A6].
- Tucker's Geodesic Sensor Net [A5] commercialized as Electrical Geodesics,
  Inc. (EGI) is the direct ancestor of the FreeEEG128 cap + belt-pack amp
  form factor. EGI built the **second 256-channel system** in the world;
  project owner M. Hough was first software engineering manager there in
  the 1990s during that build. **Ramesh Srinivasan** (Nunez's co-author on
  [A2]; now Prof. Cognitive Sciences & Biomedical Engineering at UC Irvine,
  Human Neuroscience Laboratory <https://hnl.ss.uci.edu/>) was an early
  part of EGI — the bridge by which the Nunez biophysical framework
  entered EGI's product line.

## Platform papers (Open Ephys, OpenBCI, PiEEG, BIOADC)

Siegle et al. anchor the Open Ephys platform [1]; its ripple-detector and
OPETH plugins [2,3] document GUI extensibility. OpenBCI characterization and
cEEGrid/ear adapters [4,5,6] establish the 8-16-channel reference point we
are exceeding. Gargiulo's BIOADC [7] is the closest prior-art open 32-ch
EEG with full schematic/firmware release. The PANDABox remote-EEG
protocol [8] shows the usability bar for home-deployable rigs.

## Dry / high-density electrode validation

Lopez-Gordo's review [9] remains the canonical dry-electrode survey.
Fiedler's 256-ch dry cap and multi-centre evaluation [10,11] plus Heijs
et al.'s soft multipin validation [12] define signal-quality expectations
at 128+ ch. Ehrhardt and Kleeva cross-compare dry vs. wet ERPs and
resting spectra [13,14]. Warsito's flower electrode [15] and Erickson's
MXene array [16] are the closest 2023-24 analogues for beta-generation
dry sensors.

## Amplifier / ADC / front-end design

Liu's 35 nV/√Hz AFE in 40 nm CMOS [17] and Papadopoulou's 512-ch modular
ASIC [18] bracket what a 128-ch simultaneous-sampling Δ-Σ front end must
beat for noise, power, and scaling. Knierim's systematic comparison of
high-end vs. low-cost EEG amplifiers [19] gives the benchmarking protocol
we should replicate for FreeEEG128-beta acceptance testing.

## Wireless, modular, and ambulatory EEG

Ding's modular wireless EEG sensor-network platform [20] and the ambulance
field test by Lohi et al. [21] inform the USB-tether vs. Bluetooth/Wi-Fi
trade for the beta enclosure. Epinat-Duclos [22] provides a portable-vs-
wired comparison protocol (EPOC Flex, LiveAmp, BrainAmp) that FreeEEG128
should pass.

## Reviews and scoping

LaRocco's low-cost EEG systematic review [23] and Sabio's scoping review of
consumer-grade EEG [24] frame where FreeEEG128 sits relative to Muse/Emotiv.
The 2025 portable-dry-EEG review by Zhang et al. [25] covers the post-2020
BCI hardware landscape.

---

## Bibliography

[A1] Nunez, P.L. *Electric Fields of the Brain*. Oxford University Press (1981).

[A2] Nunez, P.L. & Srinivasan, R. *Electric Fields of the Brain: The Neurophysics of EEG*, 2nd ed. Oxford University Press (2006).

[A3] Nunez, P.L. & Westdorp, A.F. The surface Laplacian, high resolution EEG and controversies. *Brain Topogr.* **6**, 221-226 (1994). doi:10.1007/BF01187712.

[A4] Gevins, A. et al. High-resolution EEG mapping of cortical activation related to working memory. *Cereb. Cortex* **7**, 374-385 (1997). doi:10.1093/cercor/7.4.374. *(representative; Gevins authored 100+ publications)*

[A5] Tucker, D.M. Spatial sampling of head electrical fields: the geodesic sensor net. *Electroencephalogr. Clin. Neurophysiol.* **87**, 154-163 (1993). doi:10.1016/0013-4694(93)90121-B.

[A6] Pflieger, M.E. & Sands, S.F. 256-channel ERP information growth. *NeuroImage* **3**(3 Suppl.), S10 (1996). doi:10.1016/S1053-8119(96)80012-7. *Primary source for the **first 256-channel EEG system**, built at Neuroscan by Pflieger and Sands as principals.*

[A7] Schreiner, L., Jordan, M., Sieghartsleitner, S., Kapeller, C., Pretl, H., Kamada, K., Asman, P., Ince, N.F., Miller, K.J. & Guger, C. Mapping of the central sulcus using non-invasive ultra-high-density brain recordings. *Scientific Reports* **14**, 6527 (2024). doi:10.1038/s41598-024-57167-y. ***Primary paper for the g.tec g.Pangolin VHD-EEG system*** (up to 1024 channels, 8.6 mm inter-electrode, 5.9 mm diameter, flex-PCB active-wet grids, 24-bit / up to 38.4 kHz via g.HIamp). Demonstrates 95.2% anterior/posterior-to-CS classification by SSEP phase reversal — comparable to invasive ECoG.

[A8] Shirazi, S.Y., Onton, J. & Makeig, S. Simulating scalp EEG from ultrahigh-density ECoG data illustrates cortex to scalp projection patterns. *bioRxiv* 2025.06.24.660870 (2025). doi:10.1101/2025.06.24.660870. *Cortex-to-scalp projection simulations motivating the VHD-EEG density case.*

[A9] Liu, Q., Ganzetti, M., Wenderoth, N. & Mantini, D. Detecting Large-Scale Brain Networks Using EEG: Impact of Electrode Density, Head Modeling and Source Localization. *Frontiers in Neuroinformatics* **12**, 4 (2018). doi:10.3389/fninf.2018.00004. *Systematic study of density × head-model × source-localization interaction for network reconstruction.*

[1] Siegle, J.H. et al. Open Ephys: an open-source, plugin-based platform for multichannel electrophysiology. *J. Neural Eng.* **14**, 045003 (2017). doi:10.1088/1741-2552/aa5eea.

[2] de Sousa, B.M. et al. An open-source, ready-to-use and validated ripple detector plugin for the Open Ephys GUI. *bioRxiv* 2022.04.01.486754 (2022). doi:10.1101/2022.04.01.486754.

[3] Szell, A. et al. OPETH: Open Source Solution for Real-Time Peri-Event Time Histogram Based on Open Ephys. *Front. Neuroinform.* **14**, 21 (2020). doi:10.3389/fninf.2020.00021.

[4] Cardona-Alvarez, Y.N., Álvarez-Meza, A.M., Cárdenas-Peña, D.A., Castaño-Duque, G.A. & Castellanos-Domínguez, G. A Novel OpenBCI Framework for EEG-Based Neurophysiological Experiments. *Sensors* **23**(7), 3763 (2023). doi:10.3390/s23073763. **Architecture reference for open-hardware BCI frameworks.** Raspberry Pi as acquisition server (validates our Pi Zero 2W companion choice); three-layer driver design; distributed computing via Apache Kafka; marker sync via Light-Dependent Resistor (analogous to our Labstreamer photodiode); impedance via ADS1299 6 nA @ 31.25 Hz lead-off drive; 56 ms end-to-end latency with 5.7 ms wireless jitter benchmarked against BCI2000+g.USBamp and OpenViBE+TMSi. Only validated motor imagery — P300/SSVEP/N170 gap fillable by FreeEEG128. Documents the OpenBCI Cyton+Daisy 8→16 channel *interleaving* artifact (alternating samples between boards requires interpolation) — **FreeEEG128's TIM1/TIM8-synchronized 16× ADS131M08 cascade eliminates that artifact entirely**. Open source: <https://github.com/UN-GCPDS/openbci-stream>, <https://github.com/UN-GCPDS/BCI-framework>, <https://docs.bciframework.org/>.

[5] Knierim, M.T., Schemmer, M. & Bauer, N. A simplified design of a cEEGrid ear-electrode adapter for the OpenBCI biosensing platform. *HardwareX* **12**, e00357 (2022). doi:10.1016/j.ohx.2022.e00357.

[5a] Knierim, M.T., Berger, C. & Reali, P. Open-source concealed EEG data collection for Brain-computer-interfaces — neural observation through OpenBCI amplifiers with around-the-ear cEEGrid electrodes. *Brain-Computer Interfaces* **8**(4), 161-179 (2021). doi:10.1080/2326263X.2021.1972633. **Template for a FreeEEG-Ear spin-off product line.** Demonstrates that an open-hardware ADS1299-based amplifier can serve the concealed / around-the-ear form factor at clinical-grade signal quality, opening a separate application track orthogonal to high-density research rigs: ~1-minute electrode application, no hair prep, <5-minute protocols. Pairs naturally with passive paradigms like Fastball (Stothart et al.) for implicit-recognition screening that works on cognitively impaired populations where instruction-following fails — dementia, stroke, pediatric. The same ADS131M08 + STM32H743 architecture that drives FreeEEG128 at 128 ch scales cleanly *down* to a 16-20 ch cEEGrid-class board with unchanged firmware / host / packet-format / LSL stack.

[5b] Debener, S., Emkes, R., De Vos, M. & Bleichner, M.G. Unobtrusive ambulatory EEG using a smartphone and flexible printed electrodes around the ear. *Scientific Reports* **5**, 16743 (2015). doi:10.1038/srep16743. *The original cEEGrid paper.*

[5c] Stothart, G., Quadflieg, S. & Milton, A. A fast and implicit measure of semantic categorisation using steady state visual evoked potentials. *Neuropsychologia* **102**, 11-18 (2017). doi:10.1016/j.neuropsychologia.2017.05.025. *Origin of the **Fastball paradigm**: rapid serial visual presentation at 3 Hz with embedded oddball at 0.6 Hz, passive implicit-recognition response detected in <3 min, no overt task required.*

[5d] Stothart, G., Smith, L.J., Milton, A. & Coulthard, E. A passive and objective measure of recognition memory in Alzheimer's disease using Fastball memory assessment. *Brain* **144**(9), 2812-2825 (2021). doi:10.1093/brain/awab154. *Fastball applied to Alzheimer's screening — the clinical end of the cEEGrid + Fastball application pathway.*

[6] Uktveris, T. & Jusas, V. Development of a Modular Board for EEG Signal Acquisition. *Sensors* **18**, 2140 (2018). doi:10.3390/s18072140.

[7] Gargiulo, G.D. et al. Fully Open-Access Passive Dry Electrodes BIOADC: Open-Electroencephalography (EEG) Re-Invented. *Sensors* **19**, 772 (2019). doi:10.3390/s19040772.

[8] Galvez-Ortega, K. et al. Remote EEG acquisition in Angelman syndrome using PANDABox-EEG. *J. Neurodev. Disord.* **17**, 25 (2025). doi:10.1186/s11689-025-09611-x.

[9] Lopez-Gordo, M.A., Sanchez-Morillo, D. & Pelayo Valle, F. Dry EEG Electrodes. *Sensors* **14**, 12847-12870 (2014). doi:10.3390/s140712847.

[10] Fiedler, P. et al. A high-density 256-channel cap for dry electroencephalography. *Hum. Brain Mapp.* **43**, 1295-1308 (2022). doi:10.1002/hbm.25721.

[11] Ng, C.R. et al. Multi-Center Evaluation of Gel-Based and Dry Multipin EEG Caps. *Sensors* **22**, 8079 (2022). doi:10.3390/s22208079.

[12] Heijs, J.J.A. et al. Validation of Soft Multipin Dry EEG Electrodes. *Sensors* **21**, 6827 (2021). doi:10.3390/s21206827.

[13] Ehrhardt, N.M. et al. Comparison of dry and wet electroencephalography for the assessment of cognitive evoked potentials and sensor-level connectivity. *Front. Neurosci.* **18**, 1441799 (2024). doi:10.3389/fnins.2024.1441799.

[14] Kleeva, D., Ninenko, I. & Lebedev, M.A. Resting-state EEG recorded with gel-based vs. consumer dry electrodes. *Front. Neurosci.* **18**, 1326139 (2024). doi:10.3389/fnins.2024.1326139.

[15] Warsito, I.F. et al. Flower electrodes for comfortable dry electroencephalography. *Sci. Rep.* **13**, 16589 (2023). doi:10.1038/s41598-023-42732-8.

[16] Erickson, B. et al. Evaluating and benchmarking the EEG signal quality of high-density, dry MXene-based electrode arrays. *J. Neural Eng.* **21**, 016013 (2024). doi:10.1088/1741-2552/ad141e.

[17] Liu, L. et al. A 35 nV/√Hz Analog Front-End Circuit in UMC 40 nm CMOS for Biopotential Signal Acquisition. *Sensors* **24**, 7994 (2024). doi:10.3390/s24247994.

[18] Papadopoulou, A. et al. A Modular 512-Channel Neural Signal Acquisition ASIC for High-Density 4096 Channel Electrophysiology. *Sensors* **24**, 3986 (2024). doi:10.3390/s24123986.

[19] Knierim, M.T., Bleichner, M.G. & Reali, P. A Systematic Comparison of High-End and Low-Cost EEG Amplifiers for Concealed, Around-the-Ear EEG Recordings. *Sensors* **23**, 4559 (2023). doi:10.3390/s23094559.

[20] Ding, R. et al. A wireless, scalable and modular EEG sensor network platform for unobtrusive brain recordings. *bioRxiv* 2025.01.26.634908 (2025). doi:10.1101/2025.01.26.634908.

[21] Lohi, S. et al. Feasibility of recording EEG in the ambulance using a portable, wireless EEG recording system. *PLoS ONE* **20**, e0327415 (2025). doi:10.1371/journal.pone.0327415.

[22] Epinat-Duclos, J. et al. Evaluating portable EEG: a comparison between EPOC Flex, LiveAmp, and BrainAmp. *PeerJ* **14**, e20416 (2026). doi:10.7717/peerj.20416.

[23] LaRocco, J., Le, M.D. & Paeng, D.-G. A Systemic Review of Available Low-Cost EEG Headsets Used for Drowsiness Detection. *Front. Neuroinform.* **14**, 553352 (2020). doi:10.3389/fninf.2020.553352.

[24] Sabio, J. et al. A scoping review on the use of consumer-grade EEG devices for research. *PLoS ONE* **19**, e0291186 (2024). doi:10.1371/journal.pone.0291186.

[25] Zhang, M. et al. Recent Advances in Portable Dry Electrode EEG: Architecture and Applications in Brain-Computer Interfaces. *Sensors* **25**, 5215 (2025). doi:10.3390/s25165215.

<!-- Classical / seminal references (pre-2019, outside paperclip corpus). Verify DOIs manually. -->

[26] Teplan, M. Fundamentals of EEG measurement. *Meas. Sci. Rev.* **2**, 1-11 (2002).

[27] Oostenveld, R. & Praamstra, P. The five percent electrode system for high-resolution EEG and ERP measurements. *Clin. Neurophysiol.* **112**, 713-719 (2001). doi:10.1016/S1388-2457(00)00527-7.

[28] Seeck, M. et al. The standardized EEG electrode array of the IFCN. *Clin. Neurophysiol.* **128**, 2070-2077 (2017). doi:10.1016/j.clinph.2017.06.254.

[29] Metting van Rijn, A.C., Peper, A. & Grimbergen, C.A. High-quality recording of bioelectric events. Part 1: interference reduction, theory and practice. *Med. Biol. Eng. Comput.* **28**, 389-397 (1990). doi:10.1007/BF02441961.

[30] Usakli, A.B. Improvement of EEG signal acquisition: an electrical aspect for state of the art of front end. *Comput. Intell. Neurosci.* **2010**, 630649 (2010). doi:10.1155/2010/630649.

[31] Fonseca, C. et al. A novel dry active electrode for EEG recording. *IEEE Trans. Biomed. Eng.* **54**, 162-165 (2007). doi:10.1109/TBME.2006.884649.

[32] Mathewson, K.E. et al. High and dry? Comparing active dry EEG electrodes to active and passive wet electrodes. *Psychophysiology* **54**, 74-82 (2017). doi:10.1111/psyp.12536.

[33] Grozea, C., Voinescu, C.D. & Fazli, S. Bristle-sensors — low-cost flexible passive dry EEG electrodes. *J. Neural Eng.* **8**, 025008 (2011). doi:10.1088/1741-2560/8/2/025008.

[34] Chi, Y.M., Jung, T.-P. & Cauwenberghs, G. Dry-contact and noncontact biopotential electrodes. *IEEE Rev. Biomed. Eng.* **3**, 106-119 (2010). doi:10.1109/RBME.2010.2084078.

[35] Jackson, A.F. & Bolger, D.J. The neurophysiological bases of EEG and EEG measurement: a review for the rest of us. *Psychophysiology* **51**, 1061-1071 (2014). doi:10.1111/psyp.12283.

[36] Niso, G. et al. Wireless EEG: A survey of systems and studies. *NeuroImage* **269**, 119774 (2023). doi:10.1016/j.neuroimage.2022.119774.

[37] Voigts, J. et al. The flexDrive: an ultra-light implant for optical control and highly parallel chronic recording of neuronal ensembles in freely moving mice. *Front. Syst. Neurosci.* **7**, 8 (2013). doi:10.3389/fnsys.2013.00008.

<!-- PRIORITY-1 PLACEHOLDER -->

[38] Black, C., Voigts, J., Agrawal, U., Ladow, M., Santoyo, J., Moore, C. & Jones, S. Open Ephys electroencephalography (Open Ephys + EEG): a modular, low-cost, open-source solution to human neural recording. *J. Neural Eng.* **14**, 035002 (2017). doi:10.1088/1741-2552/aa651f. **Primary comparison benchmark for FreeEEG128** — see `COMPARISON.md §Black 2017 vs FreeEEG128`.
