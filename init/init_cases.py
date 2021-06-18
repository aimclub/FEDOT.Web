from app.api.showcase.schema import ShowcaseItemSchema


def create_default_cases(storage):
    scoring_case = ShowcaseItemSchema()
    storage.db.create_collection('cases')
    scoring_case.case_id = 'scoring'
    scoring_case.icon_path = './data/scoring/icon.ong'
    scoring_case.description = 'The purpose of credit scoring is to assess and ' \
                               'possibly reduce the risk of a bank associated with lending clients. ' \
                               'Risk minimization happens due to dividing potential borrowers into creditworthy ' \
                               'and non-creditworthy borrowers. ' \
                               ' Behavioural scoring involves an assessment of creditworthiness based on information ' \
                               'about the borrower, characterizing his behaviour and habits and ' \
                               'obtained from various sources.'
    scoring_case.chain_id = 'best_scoring_chain'
    storage.db.cases.insert_one(dict(scoring_case))

    # showcase = ShowcaseSchema()
    # showcase.items_uids = ['scoring']
    # storage.db.showcase.insert_one(showcase)

    return
