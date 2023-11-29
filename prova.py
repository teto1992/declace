df = pd.DataFrame(
    [
        [25, _25['asp_cost']/10, _25['heu_cost']/10, _25['declace_cost']/10],
        [50, _50['asp_cost']/10, _50['heu_cost']/10, _50['declace_cost']/10],
        [75, _75['asp_cost']/10, _75['heu_cost']/10, _75['declace_cost']/10],
        [100, _100['asp_cost']/10, _100['heu_cost']/10, _100['declace_cost']/10],
        [125, _125['asp_cost']/10, _125['heu_cost']/10, _125['declace_cost']/10],
        [150, _150['asp_cost']/10, _150['heu_cost']/10, _150['declace_cost']/10],
    ],
    columns=['nodes','asp', 'heu', 'declace']
)
