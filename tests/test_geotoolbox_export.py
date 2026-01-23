import pytest
from unittest.mock import patch, MagicMock
from modules import geotoolbox, core

class TestGeotoolboxExport:
    @pytest.fixture
    def mock_dependencies(self):
        """Mock all external dependencies of the export logic."""
        with patch('modules.geotoolbox.get_local_slope_vector') as mock_slope, \
             patch('modules.geotoolbox.get_elevation_ign_only') as mock_elev, \
             patch('modules.geotoolbox.fetch_features') as mock_fetch, \
             patch('modules.geotoolbox.calculate_geometrics') as mock_geom, \
             patch('modules.geotoolbox.generate_excel_for_layer') as mock_excel, \
             patch('modules.core.dispatch_event') as mock_dispatch, \
             patch('os.makedirs') as mock_makedirs, \
             patch('modules.geotoolbox.LAYERS_CONFIG', {
                 'TEST_LAYER': {'label': 'Layer 1', 'name_field': 'id'}
             }):
            yield {
                'slope': mock_slope,
                'elev': mock_elev,
                'fetch': mock_fetch,
                'geom': mock_geom,
                'excel': mock_excel,
                'dispatch': mock_dispatch,
                'makedirs': mock_makedirs
            }

    def test_run_export_logic_orchestration(self, mock_dependencies):
        """
        Characterization test: Verify the orchestration of export logic.
        Ensures all steps are called in the correct order with expected arguments.
        """
        # Setup Mocks
        mock_dependencies['slope'].return_value = (180.0, 5.0) # South slope, 5%
        mock_dependencies['elev'].return_value = (100.0, 'IGN')
        mock_dependencies['fetch'].return_value = [{'id': 1}] # 1 feature found
        mock_dependencies['geom'].return_value = [{'id': 1, 'z': 100}] # Processed feature
        mock_dependencies['excel'].return_value = "export.xlsx"

        # Input Data
        bbox = {'min_lat': 45.0, 'max_lat': 45.1, 'min_lon': 0.0, 'max_lon': 0.1}
        layers = ['TEST_LAYER']
        folder = "MyExport"
        base_path = "/tmp"

        # Execute
        result = geotoolbox.run_export_logic(bbox, layers, folder, base_path)

        # Verifications
        
        # 1. Directory Creation
        mock_dependencies['makedirs'].assert_called()
        
        # 2. Global Analysis Steps
        mock_dependencies['slope'].assert_called_once()
        mock_dependencies['elev'].assert_called_once()
        
        # 3. Layer Processing Loop
        mock_dependencies['fetch'].assert_called_once_with('TEST_LAYER', bbox, mode='export')
        mock_dependencies['geom'].assert_called_once()
        mock_dependencies['excel'].assert_called_once()
        
        # 4. Dispatch Events (Sampler)
        # Verify at least start, progress, and end events were dispatched
        calls = mock_dependencies['dispatch'].call_args_list
        messages = [call[0][1].get('message') for call in calls if call[0][0] == 'loader_update']
        assert any("Analyse du relief" in m for m in messages)
        assert any("Traitement Layer 1" in m for m in messages)
        assert any("Export terminé" in m for m in messages)

        # 5. Result Structure
        assert result['summary'][0]['status'] == "success"
        assert result['summary'][0]['filename'] == "export.xlsx"
        assert result['summary'][0]['count'] == 1

    def test_run_export_logic_with_custom_reporter(self, mock_dependencies):
        """
        Verify that passing a custom reporter prevents default core events.
        """
        # Setup Mocks
        mock_dependencies['slope'].return_value = (180.0, 5.0)
        mock_dependencies['elev'].return_value = (100.0, 'IGN')
        mock_dependencies['fetch'].return_value = [{'id': 1}]
        mock_dependencies['geom'].return_value = [{'id': 1, 'z': 100}]
        mock_dependencies['excel'].return_value = "export.xlsx"

        mock_reporter = MagicMock()

        # Input Data
        bbox = {'min_lat': 45.0, 'max_lat': 45.1, 'min_lon': 0.0, 'max_lon': 0.1}
        layers = ['TEST_LAYER']
        folder = "MyExport"
        base_path = "/tmp"

        # Execute with custom reporter
        geotoolbox.run_export_logic(bbox, layers, folder, base_path, reporter=mock_reporter)

        # Verifications
        
        # 1. Custom Reporter called
        mock_reporter.update.assert_called()
        
        # 2. Core Dispatch NOT called (except for other events not related to reporter?)
        # CoreEventReporter dispatch events as 'loader_update'.
        # We ensure no 'loader_update' events were dispatched via core
        
        calls = mock_dependencies['dispatch'].call_args_list
        loader_events = [call for call in calls if call[0][0] == 'loader_update']
        assert len(loader_events) == 0, "Core dispatch should not be called when custom reporter is used"

    def test_generate_excel_sis_logic(self, mock_dependencies):
        """
        Verify SIS specific logic: column exclusion and URL generation.
        """
        from modules.geotoolbox_core.exporter import generate_excel_for_layer
        
        # Test Data resembling SIS layer
        rows = [{
            'code_metier': 'SSP00046140101', 
            'nom_etablissement': 'TEST SITE',
            'id_classification': 'XYZ', # Should be dropped
            'INSEE': '12345',           # Should be dropped
            'adresse': '10 Rue Test',
            'code_postal': '75000'
        }]
        
        config = {'label': 'SIS Layer'}
        
        # We need to verify the DATAFRAME content before it is written to Excel.
        # Since generate_excel_for_layer writes to file, we can either mock pandas or check the file?
        # Checking the file logic is complex (xlsx parsing).
        # Better to spy on pd.DataFrame.to_excel or similar.
        
        with patch('pandas.DataFrame.to_excel') as mock_to_excel:
             generate_excel_for_layer(rows, 'SIS', '/tmp', config)
             
             # Get the dataframe passed to to_excel
             args, _ = mock_to_excel.call_args
             # args[0] is the writer, but df.to_excel calls writer internally?
             # No, df.to_excel(writer, ...)
             
             # Actually, simpler: generate_excel_for_layer creates DF internally.
             # We can patch pandas.DataFrame to return a Mock DF that captures operations?
             # Too complex.
             
             # Let's inspect the `df` variable inside the function? No.
             
             # We can verify by inspecting the columns passed to `to_excel` if possible.
             # df.to_excel is called on the dataframe object.
             # So mock_to_excel IS the method on the dataframe instance if we patch it on the class.
             # But a new instance is created.
             pass

        # Alternative: We trust the logic if we mock pandas.DataFrame constructor and inspect the resulting mock?
        # But we manipulate the DF (drop, rename).
        
        # Let's use a real DF and mock to_excel to capture the final DF state.
        import pandas as pd
        real_to_excel = pd.DataFrame.to_excel
        
        captured_df = None
        def capture_to_excel(self, writer, **kwargs):
            nonlocal captured_df
            captured_df = self
            return None # Don't write
            
        with patch('pandas.DataFrame.to_excel', autospec=True, side_effect=capture_to_excel):
             generate_excel_for_layer(rows, 'SIS', '/tmp', config)
             
        assert captured_df is not None
        columns = captured_df.columns.tolist()
        
        # Verify SIS Exclusions
        assert 'id_classification' not in columns
        assert 'INSEE' not in columns
        
        # Verify URL Generation
        # 'code_metier' -> 'Référence' (renamed)
        # 'fiche_georisques' -> 'Fiche GéoRisques'
        assert 'Fiche GéoRisques' in columns
        assert captured_df.iloc[0]['Fiche GéoRisques'] == "https://fiches-risques.brgm.fr/georisques/infosols/classification/SSP00046140101"

        # Verify Order: Code Postal after Adresse
        # Note: Columns are renamed. 'adresse' -> 'Adresse', 'code_postal' -> 'Code Postal'
        if 'Adresse' in columns and 'Code Postal' in columns:
            idx_addr = columns.index('Adresse')
            idx_cp = columns.index('Code Postal')
            # Assuming they are adjacent or explicitly ordered as requested
            # "Reorder columns in export (Code Postal after Adresse)"
            # This implies CP should be > Addr.
            assert idx_cp > idx_addr, "Code Postal should occur after Adresse"
            
            # If we want strictly adjacent in the specific list we defined:
            # priority_cols had: "Adresse", "Code Postal"
            # So likely they are close.


