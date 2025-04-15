# Custom Tool Enhancement

This is a custom branch where the tool was adjusted to match a specific customer use case.
The use case was to read all IOT data from an PAI system and copy it to a new APM system. However
the challenge was that the equipment numbers from the PAI and APM system are not the same.
Therefore the tooling was adjusted to have a mapping for the equipments in place.

In addition the lookup for the characteristics within the S4 system was also skipped as
all characteristics are already synced to APM. The lookup for the internal characteristic id
was then also done using the APM API.

## Usage

To-do
