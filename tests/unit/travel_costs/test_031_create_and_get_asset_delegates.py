import pandas as pd

def test_create_and_get_asset_delegates(monkeypatch, project_dir, fake_transport_zones, patch_osmdata):
    # ^^^^^ include project_dir so MOBILITY_PROJECT_DATA_FOLDER is set
    import mobility.travel_costs as mod

    travel_costs = mod.TravelCosts(fake_transport_zones, "bicycle")

    called = {}
    def fake_graph(transport_zones, osm, mode):
        called["graph_args"] = (transport_zones, osm, mode)
        return "graph.rds"

    dataframe = pd.DataFrame({"cost": [42]})
    def fake_costs(transport_zones, graph):
        called["cost_args"] = (transport_zones, graph)
        return dataframe

    monkeypatch.setattr(travel_costs, "dodgr_graph", fake_graph)
    monkeypatch.setattr(travel_costs, "dodgr_costs", fake_costs)

    res = travel_costs.create_and_get_asset()
    assert res is dataframe
    assert called["graph_args"][0] is fake_transport_zones
    assert called["graph_args"][2] == "bicycle"
    assert called["cost_args"] == (fake_transport_zones, "graph.rds")
