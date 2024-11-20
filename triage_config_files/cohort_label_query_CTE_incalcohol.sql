-- cohort includes alcohol dx but excludes alcoholic cirrhosis
-- label includes alcoholic cirrhosis and does not exclude alcohol dx

with included as ( -- including people who are alive, over 18, and have had an encounter in the last 3 years
	select 
	distinct entity_id
	from clean.encounters e
	    left join clean.demographics demo using(entity_id)    
	        left join clean.death dth using(entity_id)
	where e.ADMIT_DATE > '{as_of_date}'::date - interval '3year'
	and e.ADMIT_DATE < '{as_of_date}'::date -- All encounters in the last 3 years
	and demo.birth_date < '{as_of_date}'::date - interval '18year' -- excluding under 18 yo
	and ((dth.DEATH_DATE > '{as_of_date}'::date) or (dth.DEATH_DATE is null)) -- Alive
),
excluded as ( -- excluding people who have had a prior Alcohol cirrhosis, hep, liver, or other liver dx
	select 
	distinct entity_id 
from clean.diagnosis_mod_extended dmp 
where dmp.dx_date < '{as_of_date}'::DATE 
and (liver_comp or other_liver_comp or hepatitis or alcoholic_cirrhosis)
),
outcome_liver as ( -- everyone that has a liver complication in the next XX years including alcohol cirrhosis
    select 
    distinct entity_id
    from clean.diagnosis_mod_extended dm 
    where dm.dx_date  between '{as_of_date}'::date and ('{as_of_date}'::date + interval '{label_timespan}')
    and (dm.liver_comp or dm.alcoholic_cirrhosis)
),
outcome_other_exclude as ( -- everone that has no hep or other liver comp in the next XX years
    select 
    distinct entity_id
    from clean.diagnosis_mod_extended dm 
    where dm.dx_date  between '{as_of_date}'::date and ('{as_of_date}'::date + interval '{label_timespan}')
    and (dm.hepatitis or dm.other_liver_comp)
)
select 
    entity_id, 
    case -- people who have a liver comp but not any alcohol, hep, or other liver comps in the next XX years as 1
        when (oin.entity_id is not null) and (oex.entity_id is null) then 1 
        else 0 
    end as outcome
from included left join outcome_liver oin using(entity_id)
    left join outcome_other_exclude oex using(entity_id) 
where included.entity_id not in (select entity_id from excluded)