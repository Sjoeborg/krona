# krona

[![Release](https://img.shields.io/github/v/release/Sjoeborg/krona)](https://img.shields.io/github/v/release/Sjoeborg/krona)
[![Build status](https://img.shields.io/github/actions/workflow/status/Sjoeborg/krona/master.yml?branch=master)](https://github.com/Sjoeborg/krona/actions/workflows/master.yml?query=branch%3Amaster)
[![codecov](https://codecov.io/gh/Sjoeborg/krona/branch/main/graph/badge.svg)](https://codecov.io/gh/Sjoeborg/krona)
[![Commit activity](https://img.shields.io/github/commit-activity/m/Sjoeborg/krona)](https://img.shields.io/github/commit-activity/m/Sjoeborg/krona)
[![License](https://img.shields.io/github/license/Sjoeborg/krona)](https://img.shields.io/github/license/Sjoeborg/krona)

Transaction tool for Swedish brokers

- **Github repository**: <https://github.com/Sjoeborg/krona/>
- **Documentation** <https://Sjoeborg.github.io/krona/>

## Todo
- Fix dividend received after closed position (2016-03-23 - NOVO NORDISK AS B (DK0060534915): DIVIDEND 0.00 SEK (13.0 @ 0.00) Fees: 0.00)
- Implement more transaction types (M&A for e.g. SWMA)
- Implement realized gains for non-closed positions?
- Tweak automatic/manual resolution
- Fix position transfers between brokers by adding a new action and/or transaction_type
- What to do with GAV after reopening a closed/moved position?
- Refactor mapping so that we don't have to rely on get_synonyms
