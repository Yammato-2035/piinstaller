# KB: DEPLOY_RUNNER_INSTALL_CONSISTENCY

## Ueberblick

Read-only Cross-Validation zur Sicherstellung, dass Plan-, Validator- und Blueprint-Ebene widerspruchsfrei sind.

## Ergebnis

- `ok`: keine Widersprueche
- `review_required`: nur Review-Punkte ohne harte Policyverletzung
- `blocked`: harte Inkonsistenzen oder Sicherheitskonflikte

## API

- `POST /api/deploy/runner/install/consistency`
