# Platform discovery

| Employer | Careers page | Signatures | Public APIs | Endpoint checks |
|---|---|---|---|---|
| Société Générale | https://careers.societegenerale.com/en/search?query=intern | **taleo**: 2Fsocgen.taleo.net, socgen.taleo.net | — | — |
| BNP Paribas | https://group.bnpparibas/en/careers/all-job-offers (error: HTTPError: 403 Client Error: Forbidden for url: https://group.bnpparibas/en/careers/all-job-offers) | — | — | — |
| Natixis CIB | https://www.natixis.com/en/careers (error: ConnectionError: HTTPSConnectionPool(host='recrutement.groupebpce.com', port=443): Max retries exceeded with url: / (Caused by NameResolutionError("HTTPSConnection(host='recrutement.groupebpce.com', port=443): Failed to resolve 'recrutement.groupebpce.com' ([Errno -5] No address associated with host) | — | — | — |
| Crédit Agricole CIB | https://www.ca-cib.com/en/careers (error: ReadTimeout: HTTPSConnectionPool(host='groupecreditagricole.jobs', port=443): Read timed out. (read timeout=20)) | — | — | — |
| La Banque Postale | https://www.labanquepostale.com/recrutement.html (error: HTTPError: 404 Client Error: Not Found for url: https://www.labanquepostale.com/recrutement.html; ConnectionError: HTTPSConnectionPool(host='recrutement.labanquepostale.fr', port=443): Max retries exceeded with url: / (Caused by NameResolutionError("HTTPSConnection(host='recrutement.labanquepostale.fr', port=443): Failed to resolve 'recrutement.labanquepostale.fr' ([Errno -2] Name or service not) | — | — | — |
| HSBC Continental Europe | https://www.hsbc.fr/carrieres/ (error: HTTPError: 404 Client Error: Not Found for url: https://www.hsbc.fr/carrieres) | — | — | — |
| JPMorgan | https://www.jpmorganchase.com/careers | **oracle**: jpmc.fa.oraclecloud.com|CX_1001 | — | oracle:jpmc.fa.oraclecloud.com/CX_1001: OK, 3607 intern hits |
| Goldman Sachs | https://higher.gs.com/roles | — | — | — |
| Morgan Stanley | https://www.morganstanley.com/careers/career-opportunities-search | **eightfold**: morganstanley.eightfold.ai<br>**successfactors**: careers.morganstanley.com.cn/search/?q=, rmkcdn.successfactors.com | — | workday:ms.wd5.myworkdayjobs.com/External: OK, 630 intern hits |
| Citi | https://jobs.citi.com/ | **workday**: citi|wd5|2<br>**eightfold**: citi.eightfold.ai<br>**radancy**: /search-jobs, tbcdn.talentbrew.com | — | workday:citi.wd5.myworkdayjobs.com/2: OK, 2000 intern hits |
| Bank of America | https://careers.bankofamerica.com/ | **workday**: ghr|wd1|en-us<br>**avature**: bac.avature.net, sandboxbac.avature.net<br>**oleeo**: bankcampuscareers.tal.net<br>**cornerstone**: bankofamerica.csod.com | — | workday:ghr.wd1.myworkdayjobs.com/en-us: FAIL HTTPError: 404 Client Error: Not Found for url: https://ghr.wd1.myworkdayjobs.com/wday/cxs/ghr/en-us/jobs<br>workday:ghr.wd1.myworkdayjobs.com/Lateral-US: OK, 939 intern hits<br>workday:ghr.wd1.myworkdayjobs.com/Campus: FAIL HTTPError: 404 Client Error: Not Found for url: https://ghr.wd1.myworkdayjobs.com/wday/cxs/ghr/Campus/jobs |
| Barclays | https://search.jobs.barclays/ | **workday**: barclays|wd3|External_Career_Site_Barclays<br>**radancy**: /search-jobs, tbcdn.talentbrew.com | — | workday:barclays.wd3.myworkdayjobs.com/External_Career_Site_Barclays: OK, 651 intern hits |
| HSBC | https://mycareer.hsbc.com/en_GB/external | **avature**: /SearchJobs | — | — |
| Deutsche Bank | https://careers.db.com/students-graduates/ | — | — | workday:db.wd3.myworkdayjobs.com/DBWebsite: OK, 616 intern hits |
| UBS | https://www.ubs.com/global/en/careers/search-jobs.html | **radancy**: /search-jobs | — | workday:ubs.wd3.myworkdayjobs.com/UBS_Experienced_Careers: FAIL HTTPError: 422 Client Error: Unprocessable Entity for url: https://ubs.wd3.myworkdayjobs.com/wday/cxs/ubs/UBS_Experienced_Careers/jobs<br>workday:ubs.wd3.myworkdayjobs.com/UBS_Graduate_and_Intern_Careers: FAIL HTTPError: 422 Client Error: Unprocessable Entity for url: https://ubs.wd3.myworkdayjobs.com/wday/cxs/ubs/UBS_Graduate_and_Intern_Careers/jobs |
| Nomura | https://www.nomura.com/careers/ | **oleeo**: nomuracampus.tal.net | — | workday:nomura.wd3.myworkdayjobs.com/Nomura_Campus: FAIL HTTPError: 422 Client Error: Unprocessable Entity for url: https://nomura.wd3.myworkdayjobs.com/wday/cxs/nomura/Nomura_Campus/jobs |
| Mizuho | https://www.mizuhogroup.com/emea/careers | **successfactors**: career2.successfactors.eu, rmkcdn.successfactors.com | — | workday:mizuho.wd1.myworkdayjobs.com/mizuhoamericas: OK, 76 intern hits |
| MUFG | https://www.mufgemea.com/careers/ | **workday**: mufgub|wd3|MUFG-Careers | — | workday:mufgub.wd3.myworkdayjobs.com/MUFG-Careers: OK, 481 intern hits |
| SMBC | https://www.smbcgroup.com/emea/careers | **successfactors**: career5.successfactors.eu, career5.successfactors.eu/career?site=&amp;company=smbcP&amp;lang=en%5FGB&amp;login_ns=register&amp;career_ns=home&amp;navBarLevel=MY_PROFILE, rmkcdn.successfactors.com | — | workday:smbcgroup.wd1.myworkdayjobs.com/SMBC_Group_Careers: FAIL HTTPError: 422 Client Error: Unprocessable Entity for url: https://smbcgroup.wd1.myworkdayjobs.com/wday/cxs/smbcgroup/SMBC_Group_Careers/jobs |
| Santander CIB | https://www.santandercib.com/careers | **workday**: santander|wd3|SantanderCareers | — | workday:santander.wd3.myworkdayjobs.com/SantanderCareers: OK, 499 intern hits |
| ING | https://www.ing.jobs/global/careers.htm | **radancy**: /search-jobs, tbcdn.talentbrew.com | — | — |
| Commerzbank | https://jobs.commerzbank.com/ | — | — | — |
| Standard Chartered | https://www.sc.com/en/careers/ | **successfactors**: career2.successfactors.eu, jobs.standardchartered.com/search/?q=, rmkcdn.successfactors.com | — | workday:scb.wd3.myworkdayjobs.com/Careers: FAIL HTTPError: 422 Client Error: Unprocessable Entity for url: https://scb.wd3.myworkdayjobs.com/wday/cxs/scb/Careers/jobs |
| RBC Capital Markets | https://jobs.rbc.com/ca/en | **phenom**: cdn.phenompeople.com, phApp.ddo | — | workday:rbc.wd3.myworkdayjobs.com/RBCGLOBAL1: OK, 506 intern hits |
| Jefferies | https://www.jefferies.com/careers/ | **oleeo**: jefferies.tal.net | — | workday:jefferies.wd5.myworkdayjobs.com/JefferiesCareers: FAIL HTTPError: 422 Client Error: Unprocessable Entity for url: https://jefferies.wd5.myworkdayjobs.com/wday/cxs/jefferies/JefferiesCareers/jobs |
| Kepler Cheuvreux | https://keplercheuvreux.teamtailor.com/jobs | **teamtailor**: app, career, docs<br>**jsonld_jobposting**: "@type": "JobPosting" | **teamtailor**: keplercheuvreux (9) | — |
| Oddo BHF | https://www.oddo-bhf.com/en/careers (error: HTTPError: 404 Client Error: Not Found for url: https://www.oddo-bhf.com/en/careers) | — | — | — |
| Leonteq | https://www.leonteq.com/careers | — | — | — |
| Amundi | https://about.amundi.com/careers (error: HTTPError: 404 Client Error: Not Found for url: https://about.amundi.com/careers) | — | — | — |
| AXA IM | https://www.axa-im.com/careers | — | — | — |
| BNP Paribas AM | https://www.bnpparibas-am.com/en/careers/ | — | — | — |
| Natixis IM | https://www.im.natixis.com/en-intl/careers (error: HTTPError: 404 Client Error: Not Found for url: https://www.im.natixis.com/en-intl/careers) | — | — | — |
| Ostrum | https://www.ostrum.com/en/careers (error: HTTPError: 404 Client Error: Not Found for url: https://www.ostrum.com/en/careers) | — | — | — |
| Mirova | https://www.mirova.com/en/careers (error: HTTPError: 404 Client Error: Not Found for url: https://www.mirova.com/en/careers) | — | — | — |
| Candriam | https://www.candriam.com/en/professional/careers/ | — | — | — |
| Carmignac | https://www.carmignac.com/en/careers | — | — | — |
| Tikehau Capital | https://www.tikehaucapital.com/en/careers | — | — | — |
| Rothschild & Co | https://www.rothschildandco.com/en/careers/ | **workday**: rothschildandco|wd3|RothschildAndCo_Lateral<br>**oleeo**: rothschildandco.tal.net | — | workday:rothschildandco.wd3.myworkdayjobs.com/RothschildAndCo_Lateral: OK, 113 intern hits |
| Edmond de Rothschild | https://www.edmond-de-rothschild.com/en/careers | **oracle**: fa-evht-saasfaprod1.fa.ocs.oraclecloud.com|CX_2001 | — | oracle:fa-evht-saasfaprod1.fa.ocs.oraclecloud.com/CX_2001: FAIL ConnectionError: HTTPSConnectionPool(host='fa-evht-saasfaprod1.fa.ocs.oraclecloud.com', port=443): Max retries exceeded with url: /hcmRestApi/resources/latest/recruitingCEJobRequisitions?onlyData=true |
| Lazard | https://www.lazard.com/careers/ | **oracle**: icbpjb.fa.ocs.oraclecloud.com|LazardProfessionalCareers, icbpjb.fa.ocs.oraclecloud.com|LazardStudentCareers | — | oracle:icbpjb.fa.ocs.oraclecloud.com/LazardProfessionalCareers: OK, 92 intern hits<br>oracle:icbpjb.fa.ocs.oraclecloud.com/LazardStudentCareers: OK, 92 intern hits |
| BlackRock | https://careers.blackrock.com/ | **radancy**: /search-jobs, tbcdn.talentbrew.com | — | workday:blackrock.wd1.myworkdayjobs.com/BlackRock_Professional: OK, 165 intern hits<br>workday:blackrock.wd1.myworkdayjobs.com/BlackRock_Campus: FAIL HTTPError: 404 Client Error: Not Found for url: https://blackrock.wd1.myworkdayjobs.com/wday/cxs/blackrock/BlackRock_Campus/jobs |
| Schroders | https://www.schroders.com/en/global/individual/careers/ | **oracle**: ekbq.fa.em2.oraclecloud.com|CX_2 | — | oracle:ekbq.fa.em2.oraclecloud.com/CX_2: OK, 60 intern hits |
| Man Group | https://www.man.com/careers | **greenhouse**: mangroup | **greenhouse**: mangroup (58) | — |
| CFM | https://www.cfm.com/careers/ (error: HTTPError: 404 Client Error: Not Found for url: https://www.cfm.com/careers/) | — | **greenhouse**: cfm (9) | — |
| Citadel | https://www.citadel.com/careers/open-opportunities/ (error: HTTPError: 403 Client Error: Forbidden for url: https://www.citadel.com/careers/open-opportunities/) | — | — | — |
| Citadel Securities | https://www.citadelsecurities.com/careers/open-opportunities/ (error: HTTPError: 403 Client Error: Forbidden for url: https://www.citadelsecurities.com/careers/open-opportunities/) | — | — | — |
| Millennium | https://www.mlp.com/careers/ | **eightfold**: app.eightfold.ai, mlp.eightfold.ai | — | — |
| Squarepoint | https://www.squarepoint-capital.com/careers (error: HTTPError: 404 Client Error: Not Found for url: https://www.squarepoint-capital.com/careers) | — | **greenhouse**: squarepointcapital (92) | — |
| Qube Research & Technologies | https://www.qube-rt.com/careers | — | **greenhouse**: quberesearchandtechnologies (193) | — |
| Jane Street | https://www.janestreet.com/join-jane-street/open-roles/ | — | **greenhouse**: janestreet (219) | — |
| Optiver | https://optiver.com/working-at-optiver/career-opportunities/ | **jsonld_jobposting**: "@type":"JobPosting" | **greenhouse**: optiverus (168) | — |
| IMC | https://www.imc.com/eu/careers/jobs (error: HTTPError: 404 Client Error: Not Found for url: https://www.imc.com/eu/careers/jobs) | — | **greenhouse**: imc (170) | — |
| Susquehanna (SIG) | https://careers.sig.com/ | **icims**: cookie-policy-scripts.icims.com, sig.icims.com, www.icims.com | — | — |
| Flow Traders | https://www.flowtraders.com/careers | — | **greenhouse**: flowtraders (45) | — |
| Hudson River Trading | https://www.hudsonrivertrading.com/careers/ (error: HTTPError: 403 Client Error: Forbidden for url: https://www.hudsonrivertrading.com/careers/) | — | **greenhouse**: wehrtyou (88) | — |
| DRW | https://drw.com/work-at-drw/listings | — | **greenhouse**: drweng (168) | — |
| Two Sigma | https://careers.twosigma.com/careers/SearchJobs (error: HTTPError: 404 Client Error: Not Found for url: https://careers.twosigma.com/careers/SearchJobs/) | — | — | — |
| G-Research | https://www.gresearch.com/join-us/ | — | — | — |
| Marshall Wace | https://www.mwam.com/careers/ (error: HTTPError: 404 Client Error: Not Found for url: https://www.mwam.com/careers/) | — | **greenhouse**: marshallwace (1) | — |
| Brevan Howard | https://www.brevanhoward.com/careers/ | **phenom**: cdn.phenompeople.com, phApp.ddo | — | — |
| Tower Research | https://www.tower-research.com/open-positions | **greenhouse**: towerresearchcapital | **greenhouse**: towerresearchcapital (101) | — |
| Jump Trading | https://www.jumptrading.com/careers/ | **greenhouse**: talent_community | **greenhouse**: jumptrading (95) | — |
| Murex | https://www.murex.com/en/careers (error: HTTPError: 404 Client Error: Not Found for url: https://www.murex.com/en/careers) | — | — | — |
| Numerix | https://www.numerix.com/company/careers (error: HTTPError: 404 Client Error: Not Found for url: https://www.numerix.com/company/careers) | — | **greenhouse**: numerix (7) | — |
| AXA | https://www.axa.com/en/careers | **icims**: careers-en-axa.icims.com, cookie-policy-scripts.icims.com, move-en-axa.icims.com | — | — |
| CNP Assurances | https://www.cnp.fr/le-groupe-cnp-assurances/carrieres (error: HTTPError: 404 Client Error: Not Found for url: https://www.cnp.fr/le-groupe-cnp-assurances/carrieres) | — | — | — |
| Allianz | https://careers.allianz.com/en_US/allianz-careers.html (error: HTTPError: 404 Client Error: Not Found for url: https://careers.allianz.com/en_US/allianz-careers.html; ConnectionError: HTTPSConnectionPool(host='jobs.allianz.com', port=443): Max retries exceeded with url: / (Caused by NameResolutionError("HTTPSConnection(host='jobs.allianz.com', port=443): Failed to resolve 'jobs.allianz.com' ([Errno -3] Temporary failure in name resolution)"))) | — | — | — |
| SCOR | https://www.scor.com/en/careers | **oracle**: fa-errt-saasfaprod1.fa.ocs.oraclecloud.com|CX_2001 | — | oracle:fa-errt-saasfaprod1.fa.ocs.oraclecloud.com/CX_2001: OK, 145 intern hits |
| Banque de France | https://www.banque-france.fr/fr/banque-de-france/nous-rejoindre (error: HTTPError: 404 Client Error: Not Found for url: https://www.banque-france.fr/fr/banque-de-france/nous-rejoindre) | — | — | — |
| BCE (ECB) | https://talent.ecb.europa.eu/careers | **avature**: /SearchJobs | — | — |
| AMF | https://www.amf-france.org/fr/lamf/nous-rejoindre (error: HTTPError: 404 Client Error: Not Found for url: https://www.amf-france.org/fr/lamf/nous-rejoindre) | — | — | — |
| Deloitte | https://www2.deloitte.com/fr/fr/careers/careers.html (error: HTTPError: 404 Client Error: Not Found for url: https://www.deloitte.com/fr/fr/careers/careers.html) | — | — | — |
| EY | https://careers.ey.com/ey/search/?q=intern | **successfactors**: career5.successfactors.eu, ey/search/?q=, rmkcdn.successfactors.com | — | — |
| KPMG | https://kpmg.com/fr/fr/carrieres.html | **radancy**: /search-jobs, tbcdn.talentbrew.com | — | — |
| PwC | https://www.pwc.fr/fr/carrieres.html (error: HTTPError: 404 Client Error: Not Found for url: https://www.pwc.fr/fr/carrieres.html) | — | — | — |
| Forvis Mazars | https://www.forvismazars.com/fr/fr/carrieres | **smartrecruiters**: MAZARS | **greenhouse**: forvismazars (143)<br>**teamtailor**: forvismazars (1) | — |
| Finalyse | https://www.finalyse.com/careers (error: HTTPError: 404 Client Error: Not Found for url: https://www.finalyse.com/careers) | — | — | — |
| Julius Baer | https://www.juliusbaer.com/en/careers/ (error: HTTPError: 403 Client Error: Forbidden for url: https://www.juliusbaer.com/en/careers/) | — | — | — |
| Pictet | https://www.group.pictet/careers | **successfactors**: career012.successfactors.eu/career?company&#61;banquepict, career012.successfactors.eu/career?company=banquepict, career012.successfactors.eu/career?company=banquepict\&#34; | — | — |
| Lombard Odier | https://www.lombardodier.com/careers (error: HTTPError: 404 Client Error:  for url: https://www.lombardodier.com/careers) | — | — | — |
| Vontobel | https://www.vontobel.com/en-ch/about-vontobel/careers/ | **workday**: vontobel|wd3|Vontobel_External_Career | — | workday:vontobel.wd3.myworkdayjobs.com/Vontobel_External_Career: OK, 30 intern hits |
| Swissquote | https://careers.swissquote.com/ (error: ConnectionError: HTTPSConnectionPool(host='careers.swissquote.com', port=443): Max retries exceeded with url: / (Caused by NameResolutionError("HTTPSConnection(host='careers.swissquote.com', port=443): Failed to resolve 'careers.swissquote.com' ([Errno -2] Name or service not known)"))) | — | — | — |
| Banque Cantonale Vaudoise | https://www.bcv.ch/en/La-BCV/Carriere (error: HTTPError: 404 Client Error: Not Found for url: https://www.bcv.ch/en/home/la-bcv/carriere.html) | — | — | — |
| Zürcher Kantonalbank | https://www.zkb.ch/en/careers.html (error: HTTPError: 404 Client Error: Not Found for url: https://www.zkb.ch/en/careers.html) | — | — | — |
| EFG International | https://www.efginternational.com/careers (error: HTTPError: 403 Client Error: Forbidden for url: https://www.efginternational.com/careers) | — | — | — |
| BGL BNP Paribas | https://www.bgl.lu/en/careers.html (error: HTTPError: 404 Client Error: Not Found for url: https://www.bgl.lu/en/careers.html) | — | — | — |
| Spuerkeess (BCEE) | https://www.spuerkeess.lu/en/careers/ | — | — | — |
| Banque Internationale à Luxembourg | https://www.bil.com/en/careers (error: HTTPError: 404 Client Error: NOT FOUND for url: https://www.bil.com/en/careers) | — | — | — |
| Société Générale Luxembourg | https://www.societegenerale.lu/en/careers/ (error: HTTPError: 404 Client Error: Not Found for url: https://www.societegenerale.lu/en/careers/) | — | — | — |
| Amundi Luxembourg | https://www.amundi.lu/ | — | — | — |
| BEI (EIB) | https://www.eib.org/en/about/careers/index | — | — | — |
| KBC | https://www.kbc.com/en/careers.html (error: HTTPError: 404 Client Error: Not Found for url: https://www.kbc.com/en/careers.html) | — | — | — |
| Belfius | https://www.belfius.be/about-us/en/careers (error: HTTPError: 404 Client Error: Not Found for url: https://www.belfius.be/about-us/en/careers) | — | — | — |
| BNP Paribas Fortis | https://www.bnpparibasfortis.be/en/jobs (error: HTTPError: 503 Server Error: Service Unavailable for url: https://www.bnpparibasfortis.be/en/jobs) | — | — | — |
| Euroclear | https://www.euroclear.com/about/en/careers.html | **oracle**: don.fa.em2.oraclecloud.com|CX_1003 | — | oracle:don.fa.em2.oraclecloud.com/CX_1003: OK, 55 intern hits |
| Degroof Petercam | https://www.degroofpetercam.com/en-be/careers (error: HTTPError: 404 Client Error: Not Found for url: https://www.degroofpetercam.com/en-be/careers) | — | — | — |
| DZ Bank | https://www.karriere.dzbank.de/ | **successfactors**: career5.successfactors.eu, rmkcdn.successfactors.com | — | — |
| LBBW | https://www.lbbw.de/karriere | **successfactors**: career5.successfactors.eu, rmkcdn.successfactors.com | — | — |
| ABN AMRO | https://www.abnamro.com/en/careers (error: HTTPError: 503 Server Error: Service Unavailable for url: https://www.abnamro.com/en/careers) | — | — | — |
| Rabobank | https://rabobank.jobs/en/ (error: HTTPError: 403 Client Error: Forbidden for url: https://rabobank.jobs/en/) | — | — | — |
| Intesa Sanpaolo | https://www.intesasanpaolo.com/en/careers (error: HTTPError: 404 Client Error: Not Found for url: https://www.intesasanpaolo.com/en/careers) | — | — | — |
| UniCredit | https://careers.unicredit.eu/ | **avature**: /SearchJobs | — | — |
| BBVA | https://careers.bbva.com/ | **workday**: bbva|wd3|es | — | workday:bbva.wd3.myworkdayjobs.com/es: FAIL HTTPError: 404 Client Error: Not Found for url: https://bbva.wd3.myworkdayjobs.com/wday/cxs/bbva/es/jobs |
| BRI (BIS) | https://www.bis.org/careers/index.htm | — | — | — |
| FMI (IMF) | https://www.imf.org/en/About/Recruitment (error: HTTPError: 404 Client Error: Not Found for url: https://www.imf.org/en/About/Recruitment) | — | — | — |
| Banque mondiale | https://www.worldbank.org/en/about/careers | **cornerstone**: api.csod.com, worldbankgroup.csod.com | — | — |
