select 
entity_id, 
coalesce(bool_or(first_liver_outcome_date < '{as_of_date}'::date + '{label_timespan}'::interval and first_liver_outcome_date > '{label_timespan}'::date), false) as outcome
from clean.biopsy_labels bl left join analysis.entity_earliest_exclusion_and_outcome_dates ex using(entity_id)
where order_date > '{as_of_date}'::date
and order_date < '{as_of_date}'::date + '6month'::interval
-- and (ex.first_exclusion_date > '{as_of_date}' or ex.first_exclusion_date is null)
and entity_id is not null
and mash = 'Y'
group by 1