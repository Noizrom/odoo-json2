# Sample Employee Data (ID: 110)

| Field Name | Label | Type | Sample Value (Raw) | Sample Value (Display) | Related Model |
|---|---|---|---|---|---|
| `citizenship` | Citizenship | selection | `filipino` | `filipino` |  |
| `civil_status` | Civil Status | selection | `single` | `single` |  |
| `company_id` | Company | many2one | `1` | `Philippine Statistics Authority` | res.company |
| `date_of_birth` | Date of Birth | date | `1964-08-13` | `1964-08-13` |  |
| `father_first_name` | Father's First Name | char | `Peter` | `Peter` |  |
| `father_surname` | Father's Surname | char | `Barker` | `Barker` |  |
| `first_name` | First Name | char | `Kelsey` | `Kelsey` |  |
| `gender` | Sex at Birth | selection | `female` | `female` |  |
| `height` | Height | float | `1.82` | `1.82` |  |
| `mother_first_name` | Mother's First Name | char | `Carol` | `Carol` |  |
| `mother_surname` | Mother's Surname | char | `Baldwin` | `Baldwin` |  |
| `p_address_barangay_id` | Permanent Barangay | many2one | `48790` | `Sapang` | psa.psgc |
| `p_address_city_id` | Permanent City/Municipality | many2one | `45898` | `MANAOAG` | psa.psgc |
| `p_address_house_no` | Permanent House/Block/Lot No. | char | `1650` | `1650` |  |
| `p_address_province_id` | Permanent Province | many2one | `45873` | `PANGASINAN` | psa.psgc |
| `p_address_street` | Permanent Street | char | `Chris Skyway` | `Chris Skyway` |  |
| `p_address_zip` | Permanent ZIP Code | char | `5657` | `5657` |  |
| `r_address_barangay_id` | Residential Barangay | many2one | `49364` | `San Rufino (Pob.)` | psa.psgc |
| `r_address_city_id` | Residential City/Municipality | many2one | `45813` | `SAN NICOLAS` | psa.psgc |
| `r_address_house_no` | Residential House/Block/Lot No. | char | `0073` | `0073` |  |
| `r_address_province_id` | Residential Province | many2one | `45793` | `ILOCOS NORTE` | psa.psgc |
| `r_address_street` | Residential Street | char | `Donna Divide` | `Donna Divide` |  |
| `r_address_zip` | Residential ZIP Code | char | `0764` | `0764` |  |
| `surname` | Surname | char | `Barker` | `Barker` |  |
| `weight` | Weight | float | `74.91` | `74.91` |  |