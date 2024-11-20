create schema if not exists clean;

drop table if exists clean.most_recent_fib4_biopsy_cohort;

create table clean.most_recent_fib4_biopsy_cohort as (
    select 
        plt.entity_id, 
        plt.as_of_date,
        plt.specimen_date as plt_date,
        plt.result_num as platelets,
        plt.days_since_lab as days_since_plt,
        ast.specimen_date as ast_date,
        ast.result_num as ast,
        ast.days_since_lab as days_since_ast,
        alt.specimen_date as alt_date,
        alt.result_num as alt,
        alt.days_since_lab as days_since_alt,
        case 
            when (plt.specimen_date = ast.specimen_date) and (plt.specimen_date = alt.specimen_date) and (ast.specimen_date = alt.specimen_date) 
            then true else false 
        end all_tests_same_day,
        greatest (plt.specimen_date, alt.specimen_date, ast.specimen_date) as latest_date,
        least(plt.specimen_date, alt.specimen_date, ast.specimen_date) as first_date,
        greatest(
            abs(plt.specimen_date - alt.specimen_date),
            abs(plt.specimen_date - ast.specimen_date),
            abs(alt.specimen_date - ast.specimen_date)
        ) as gap_between_tests,
        case 
            when plt.result_num!=0 and alt.result_num!=0 
            then round(cast((extract(year from age(plt.specimen_date::date, d.birth_date::date)) * AST.result_num) / ((plt.result_num) * SQRT(ALT.result_num)) as numeric),2) 
        end AS fib4
    from clean.most_recent_labs_biopsy_cohort plt left join clean.most_recent_labs_biopsy_cohort ast 
    on plt.entity_id = ast.entity_id
    and plt.as_of_date = ast.as_of_date
    and ast.lab_type = 'ast'
        left join clean.most_recent_labs alt 
        on plt.entity_id = alt.entity_id
        and plt.as_of_date = alt.as_of_date 
        and alt.lab_type = 'alt'
            left join clean.demographics d on plt.entity_id = d.entity_id 
    where plt.lab_type = 'platelet' 
);


create index on clean.most_recent_fib4_biopsy_cohort(entity_id);
create index on clean.most_recent_fib4_biopsy_cohort(as_of_date);
create index on clean.most_recent_fib4_biopsy_cohort(days_since_plt);
create index on clean.most_recent_fib4_biopsy_cohort(days_since_alt);
create index on clean.most_recent_fib4_biopsy_cohort(days_since_ast);
create index on clean.most_recent_fib4_biopsy_cohort(gap_between_tests);