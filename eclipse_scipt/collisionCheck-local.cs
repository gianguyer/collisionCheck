using System;
using System.ComponentModel;
using System.Diagnostics;
using System.IO;
using System.Linq;
using System.Reflection;
using System.Text;
using System.Threading;
using System.Threading.Tasks;
using System.Windows;
using System.Windows.Controls;
using System.Windows.Media;
using System.Windows.Media.Media3D;
using System.Collections.Generic;
using VMS.TPS.Common.Model.API;
using VMS.TPS.Common.Model.Types;
using System.Windows.Controls.Primitives;
using System.Xml;

[assembly: AssemblyVersion("1.0.0.1")]
[assembly: ESAPIScript(IsWriteable = true)]

namespace VMS.TPS
{

    public struct BlenderSettings
    {
        public bool headplate;
        public bool laserguard;
        public bool patientmodel;

        public string sex;
        public string arms;
        public string size;

        public double pitch;
        public double roll;
        public double rot;
        public double lat;
        public double vrt;
        public double lng;

        public double tableSafetyDistance;
        public double bodySafetyDistance;

        public double tol_pitch;
        public double tol_roll;
        public double tol_rot;
        public double tol_lat;
        public double tol_vrt;
        public double tol_lng;

        override public string ToString()
        {
            StringBuilder sb = new StringBuilder();
            sb.AppendLine("headplate         = " + headplate.ToString());
            sb.AppendLine("laserguard        = " + laserguard.ToString());
            sb.AppendLine("patientmodel      = " + patientmodel.ToString());
            return sb.ToString();
        }
        public static BlenderSettings read(string path)
        {
            Dictionary<string, string> d = Util.readPropertiesFile(path);

            BlenderSettings s;
            s.headplate = d["headplate"] == "True";
            s.laserguard = d["laserguard"] == "True";
            s.patientmodel = d["patientmodel"] == "True";
            s.sex = d["sex"];
            s.size = d["size"];
            s.arms = d["arms"];
            s.pitch = double.Parse(d["pitch"]);
            s.roll = double.Parse(d["roll"]);
            s.rot = double.Parse(d["rot"]);
            s.lat = double.Parse(d["lat"]);
            s.vrt = double.Parse(d["vrt"]);
            s.lng = double.Parse(d["lng"]);

            s.tol_pitch = 0;
            s.tol_roll = 0;
            s.tol_rot = 0;
            s.tol_lat = 0;
            s.tol_vrt = 0;
            s.tol_lng = 0;

            s.tableSafetyDistance = double.Parse(d["table"]);
            s.bodySafetyDistance = double.Parse(d["body"]);

            return s;
        }
    }

    public struct TrackPoint
    {
        public double gantry, table, collimator;
        public double jawX1, jawX2, jawY1, jawY2;
        public double isoX, isoY, isoZ;
    }

    public class Script
    {
        ScriptContext scriptContext;

        string studyName;
        string patientName;
        string planName;
        string studyDir;

        string localDir = "d:\\klik\\dev\\collisionCheck-main";
		string blenderTask = "collisionMap";

        Window wind;

        bool debug = true;

        public Script()
        {
        }

        public void Execute(ScriptContext context, Window window)
        {
            scriptContext = context;
            patientName = getPatientName(context.Patient);
            planName = getPlanName(context);

            initWindow(context, window);
            wind = window;
        }

        string getPatientName(Patient patient)
        {
            return patient.LastName + "_" + patient.FirstName;
        }

        string getPlanName(ScriptContext context)
        {
            return context.Course.Id + "-" + context.ExternalPlanSetup.Id;
        }
        //  Run pathCheck

        void runBlender()
        {
            string cmd = localDir.Replace('\\' , '/') + "/code/run-blender " + studyName + " " + patientName + " " + planName + " " + blenderTask;

            runBashCommand(cmd);
        }

        //==================================================================================================
        //  Blender
        //==================================================================================================

        //  Write blender file to disk

        void writeBlenderSettings(BlenderSettings settings)
        {
            
            string settingFile = studyDir + "\\blender.properties";

            using (StreamWriter w = new StreamWriter(settingFile))
            {
                w.Write("[CollisionModel]\n");
                w.Write("headplate = " + settings.headplate.ToString() + "\n");
                w.Write("laserguard = " + settings.laserguard.ToString() + "\n");
                w.Write("patientmodel = " + settings.patientmodel.ToString() + "\n\n");
                w.Write("[PatientModel]\n");
                w.Write("sex = " + settings.sex + "\n");
                w.Write("size = " + settings.size + "\n");
                w.Write("arms = " + settings.arms + "\n\n");
                w.Write("[StartingPosition]\n");
                w.Write("pitch = " + settings.pitch.ToString() + "\n");
                w.Write("roll = " + settings.roll.ToString() + "\n");
                w.Write("rot = " + settings.rot.ToString() + "\n");
                w.Write("lat = " + settings.lat.ToString() + "\n");
                w.Write("vrt = " + settings.vrt.ToString() + "\n");
                w.Write("lng = " + settings.lng.ToString() + "\n\n");
                w.Write("[Tolerance]\n");
                w.Write("pitch = " + settings.tol_pitch.ToString() + "\n");
                w.Write("roll = " + settings.tol_roll.ToString() + "\n");
                w.Write("rot = " + settings.tol_rot.ToString() + "\n");
                w.Write("lat = " + settings.tol_lat.ToString() + "\n");
                w.Write("vrt = " + settings.tol_vrt.ToString() + "\n");
                w.Write("lng = " + settings.tol_lng.ToString() + "\n\n");
                w.Write("[SafetyDistance]\n");
                w.Write("table = " + settings.tableSafetyDistance.ToString() + "\n");
                w.Write("body = " + settings.bodySafetyDistance.ToString() + "\n");
            }
        }

        //  Read blender settings from file

        BlenderSettings readBlenderSettings()
        {
            return BlenderSettings.read(studyDir + "\\blender.properties");
        }

        //==================================================================================================
        //  Bash
        //==================================================================================================


        void runBashCommand(string cmd)
        {
            if (debug) MessageBox.Show(cmd, "Bash command");

            Process proc = new Process();
            proc.StartInfo.FileName = "c:/opt/cygwin/bin/bash";
            proc.StartInfo.Arguments = "-l -c \"" + cmd + "\"";
            proc.StartInfo.UseShellExecute = true;
            proc.Start();
            proc.WaitForExit();
        }

        //==================================================================================================
        //  Studies
        //==================================================================================================

        string[] getStudyNames()
        {
            string[] studies = Util.getSubDirs(localDir + "\\studies");
            int pos = Array.IndexOf(studies, "demo");
            if (pos >= 0)
            {
                string demo = studies[pos];
                for (int i = pos; i > 0; i--)
                    studies[i] = studies[i - 1];
                studies[0] = demo;
            }
            else
            {
                studies = studies.Concat(new string[] {"demo"}).ToArray();
            }
            return studies;
        }


        //==================================================================================================
        //  GUI
        //==================================================================================================
        void initWindow(ScriptContext context, Window window)
        {
            string[] studies = getStudyNames();
			studyName = "demo";
            studyDir = localDir + "\\studies\\" + "demo" + "\\" + patientName + "\\" + planName;

            window.WindowStartupLocation = WindowStartupLocation.CenterScreen;
            window.Width = 350;
            window.Height = 200;
            window.Title = "Collision Check - " + patientName;
            window.SizeToContent = SizeToContent.WidthAndHeight;

            Thickness margin = new Thickness(5);

            GridLength gridLength = new GridLength(50);

            StackPanel panel = new StackPanel();
            window.Content = panel;

            StackPanel idPanel = new StackPanel();
            idPanel.Orientation = Orientation.Horizontal;
            panel.Children.Add(idPanel);

            Label studyLabel = new Label();
            studyLabel.Content = "Study";
            studyLabel.Margin = margin;
            ComboBox studyCombo = new ComboBox();
            foreach (string study in studies)
                studyCombo.Items.Add(study);
            studyCombo.SelectedIndex = 0;
            studyCombo.Margin = margin;
            studyCombo.Padding = new Thickness(5);
            Button studyNewButton = new Button();
            studyNewButton.Content = "New";
            studyNewButton.Width = 50;
            studyNewButton.Margin = margin;
            studyNewButton.Padding = new Thickness(5);
            StackPanel studyPanel = new StackPanel();
            studyPanel.Orientation = Orientation.Horizontal;
            studyPanel.Margin = margin;
            panel.Children.Add(studyPanel);
            studyPanel.Children.Add(studyLabel);
            studyPanel.Children.Add(studyCombo);
            studyPanel.Children.Add(studyNewButton);
			
            studyCombo.SelectionChanged += (s, ev) =>
            {
                studyName = studyCombo.SelectedValue.ToString();
                studyDir = localDir + "\\studies\\" + studyName + "\\" + patientName + "\\" + planName;
            };

            studyNewButton.Click += (s, ev) =>
            {

                string newItem = dialogAddStudy();
                if (!string.IsNullOrWhiteSpace(newItem))
                {
                    // Add the new item to the dropdown menu
                    studyCombo.Items.Add(newItem);

                    // Set the selected item to the newly added item
                    studyCombo.SelectedItem = newItem;
                }
            };

            Label taskLabel = new Label();
            taskLabel.Content = "Study";
            taskLabel.Margin = margin;
            ComboBox taskCombo = new ComboBox();
            taskCombo.Items.Add("collisionMap");
			taskCombo.Items.Add("pathCheck");
            taskCombo.SelectedIndex = 0;
            taskCombo.Margin = margin;
            taskCombo.Padding = new Thickness(5);
            StackPanel taskPanel = new StackPanel();
            taskPanel.Orientation = Orientation.Horizontal;
            taskPanel.Margin = margin;
            panel.Children.Add(taskPanel);
            taskPanel.Children.Add(taskLabel);
            taskPanel.Children.Add(taskCombo);
			
            taskCombo.SelectionChanged += (s, ev) =>
            {
                blenderTask = taskCombo.SelectedValue.ToString();
            };

            GroupBox settingsGroup = new GroupBox();
            settingsGroup.Header = "Settings";
            settingsGroup.Padding = margin;
            panel.Children.Add(settingsGroup);

            StackPanel settingsPanel = new StackPanel();
            settingsGroup.Content = settingsPanel;

            CheckBox cbHeadPlate = addCheckBox(settingsPanel, "Head plate");
            CheckBox cbLaserguard = addCheckBox(settingsPanel, "Laserguard");
            CheckBox cbPatientmodel = addCheckBox(settingsPanel, "Patient model");

            Grid settingsGrid = new Grid();
            settingsPanel.Children.Add(settingsGrid);
            settingsGrid.HorizontalAlignment = HorizontalAlignment.Left;
            settingsGrid.ColumnDefinitions.Add(new ColumnDefinition());
            settingsGrid.ColumnDefinitions.Add(new ColumnDefinition());

            ComboBox sexCombo = addCombo(settingsGrid, "Sex", new string[] { "M", "F"});
            ComboBox sizeCombo = addCombo(settingsGrid, "Size", new string[] { "Small", "Large" });
            ComboBox armsCombo = addCombo(settingsGrid, "Arms", new string[] { "Down", "Up" });

            foreach (FrameworkElement e in settingsPanel.Children)
                e.Margin = margin;
            GroupBox tableGroup = new GroupBox();
            tableGroup.Header = "Table";
            tableGroup.Padding = margin;
            panel.Children.Add(tableGroup);

            Grid tableGrid = new Grid();
            tableGroup.Content = tableGrid;
            tableGrid.HorizontalAlignment = HorizontalAlignment.Left;
            tableGrid.ColumnDefinitions.Add(new ColumnDefinition());
            tableGrid.ColumnDefinitions.Add(new ColumnDefinition());

            ComboBox tableSettingCombo = addCombo(tableGrid, "Table position", new string[] { "Absolute", "Relative" });

            Label lbLat = addLabel(tableGrid, "Lateral");
            TextBox tbLat = addTextBox(tableGrid);
            Label lbVrt = addLabel(tableGrid, "Vertical");
            TextBox tbVrt = addTextBox(tableGrid);
            Label lbLng = addLabel(tableGrid, "Longitudinal");
            TextBox tbLng = addTextBox(tableGrid);

            GroupBox marginGroup = new GroupBox();
            marginGroup.Header = "Additional margins";
            marginGroup.Padding = margin;
            panel.Children.Add(marginGroup);

            Grid marginGrid = new Grid();
            marginGroup.Content = marginGrid;
            marginGrid.HorizontalAlignment = HorizontalAlignment.Left;
            ColumnDefinition margincolumn = new ColumnDefinition();
            margincolumn.Width = gridLength;
            marginGrid.ColumnDefinitions.Add(new ColumnDefinition());
            marginGrid.ColumnDefinitions.Add(margincolumn);
            marginGrid.ColumnDefinitions.Add(new ColumnDefinition());

            TextBox tbTableMargin = addTextBox(marginGrid, "Table", "0.0", "cm");
            TextBox tbBodyMargin = addTextBox(marginGrid, "Patient model", "0.0", "cm");

            GroupBox toleranceGroup = new GroupBox();
            toleranceGroup.Header = "Tolerances";
            toleranceGroup.Padding = margin;
            panel.Children.Add(toleranceGroup);

            Grid toleranceGrid = new Grid();
            toleranceGroup.Content = toleranceGrid;
            toleranceGrid.HorizontalAlignment = HorizontalAlignment.Left;
            ColumnDefinition column = new ColumnDefinition();
            column.Width = gridLength;
            toleranceGrid.ColumnDefinitions.Add(new ColumnDefinition());
            toleranceGrid.ColumnDefinitions.Add(column);
            toleranceGrid.ColumnDefinitions.Add(new ColumnDefinition());

            TextBox tbTolLat = addTextBox(toleranceGrid, "Lateral", "0.0", "cm");
            TextBox tbTolVrt = addTextBox(toleranceGrid, "Vertical", "0.0", "cm");
            TextBox tbTolLng = addTextBox(toleranceGrid, "Longitudinal", "0.0", "cm");
            TextBox tbTolRot = addTextBox(toleranceGrid, "Rotation", "0.0", "°");
            TextBox tbTolRoll = addTextBox(toleranceGrid, "Roll", "0.0", "°");
            TextBox tbTolPitch = addTextBox(toleranceGrid, "Pitch", "0.0", "°");

            StackPanel buttons = new StackPanel();
            buttons.Orientation = Orientation.Horizontal;
            panel.Children.Add(buttons);
            foreach (FrameworkElement e in panel.Children)
                e.Margin = margin;

            Button ok = new Button();
            buttons.Children.Add(ok);
            ok.Content = "OK";

            Button cancel = new Button();
            buttons.Children.Add(cancel);
            cancel.Content = "Cancel";

            foreach (Button b in buttons.Children)
            {
                b.Width = 100;
                b.Margin = margin;
                b.Padding = new Thickness(5);
            }

            tableSettingCombo.SelectionChanged += (s, ev) =>
            {
                if (tableSettingCombo.SelectedIndex > 0)
                {
                    lbLat.Content = "x__iso - x__refpoint";
                    lbVrt.Content = "y__iso - y__refpoint";
                    lbLng.Content = "z__iso - z__refpoint";
                }
                else
                {
                    lbLat.Content = "Lateral";
                    lbVrt.Content = "Vertical";
                    lbLng.Content = "Longitudinal";
                }
            };

            cbPatientmodel.Click += (s, ev) =>
            {
                if (cbPatientmodel.IsChecked == false)
                {
                    sexCombo.IsEnabled = false;
                    armsCombo.IsEnabled = false;
                    sizeCombo.IsEnabled = false;
                }
                else
                {
                    sexCombo.IsEnabled = true;
                    armsCombo.IsEnabled = true;
                    sizeCombo.IsEnabled = true;
                }
            };

            BlenderSettings settings = new BlenderSettings();

            ok.Click += (s, ev) =>
            {
                settings.headplate = cbHeadPlate.IsChecked == true;
                settings.laserguard = cbLaserguard.IsChecked == true;
                settings.patientmodel = cbPatientmodel.IsChecked == true;
                settings.sex = sexCombo.SelectedItem.ToString();
                settings.arms = armsCombo.SelectedItem.ToString().ToLower();
                settings.size = sizeCombo.SelectedItem.ToString().ToLower();
                if (tableSettingCombo.SelectedIndex > 0)
                {
                    settings.lat = 8.89 - double.Parse(tbLat.Text);
                    settings.vrt = 2.0 - double.Parse(tbVrt.Text);
                    settings.lng = -18.15 - double.Parse(tbLng.Text);
                }
                else
                {
                    settings.lat = double.Parse(tbLat.Text);
                    settings.vrt = double.Parse(tbVrt.Text);
                    settings.lng = double.Parse(tbLng.Text);
                }
                settings.tableSafetyDistance = double.Parse(tbTableMargin.Text);
                settings.bodySafetyDistance = double.Parse(tbBodyMargin.Text);
                settings.tol_lat = double.Parse(tbTolLat.Text);
                settings.tol_vrt = double.Parse(tbTolVrt.Text);
                settings.tol_lng = double.Parse(tbTolLng.Text);
                settings.tol_rot = double.Parse(tbTolRot.Text);
                settings.tol_roll = double.Parse(tbTolRoll.Text);
                settings.tol_pitch = double.Parse(tbTolPitch.Text);

                window.DialogResult = true;

                Directory.CreateDirectory(studyDir);
                writeBlenderSettings(settings);

				if (blenderTask == "pathCheck") {
					writePlan(scriptContext.ExternalPlanSetup);
				}
				maybeRunSetup();
				
                window.Close();

            };
            cancel.Click += (s, ev) =>
            {
                window.Close();
            };
        }

        bool maybeRunSetup()
        {
            bool b = MessageBox.Show("Patient: " + patientName + "\nPlan: " + planName + "\n\nRun " + blenderTask + " ?", "Run " + blenderTask, MessageBoxButton.OKCancel) == MessageBoxResult.OK;
            if (b)
                runBlender();
            return b;
        }

        CheckBox addCheckBox(StackPanel panel, string text)
        {
            CheckBox cb = new CheckBox();
            cb.Content = text;
            cb.IsChecked = true;
            panel.Children.Add(cb);
            return cb;
        }
        ComboBox createCombo(string[] items)
        {
            ComboBox combo = new ComboBox();
            foreach (string it in items)
                combo.Items.Add(it);
            combo.SelectedIndex = 0;
            combo.Margin = new Thickness(2);
            return combo;
        }
        ComboBox addCombo(Grid grid, string label, string[] items)
        {
            Label lbl = new Label();
            lbl.Content = label;
            ComboBox combo = createCombo(items);
            grid.Children.Add(lbl);
            grid.Children.Add(combo);
            int row = grid.RowDefinitions.Count;
            grid.RowDefinitions.Add(new RowDefinition());
            Grid.SetColumn(lbl, 0);
            Grid.SetColumn(combo, 1);
            Grid.SetRow(lbl, row);
            Grid.SetRow(combo, row);
            return combo;
        }
        Label addLabel(Grid grid, string text)
        {
            Label label = new Label();
            label.Content = text;
            grid.Children.Add(label);
            int row = grid.RowDefinitions.Count;
            Grid.SetColumn(label, 0);
            Grid.SetRow(label, row);
            return label;
        }

        TextBox addTextBox(Grid grid)
        {
            TextBox tbox = new TextBox();
            tbox.TextAlignment = TextAlignment.Right;
            grid.Children.Add(tbox);
            int row = grid.RowDefinitions.Count;
            grid.RowDefinitions.Add(new RowDefinition());
            Grid.SetColumn(tbox, 1);
            Grid.SetRow(tbox, row);
            return tbox;
        }

        TextBox addTextBox(Grid grid, string label, string text, string unit)
        {
            Label lbl = new Label();
            lbl.Content = label;
            TextBox tbox = new TextBox();
            tbox.Text = text;
            tbox.TextAlignment = TextAlignment.Right;
            Label ulabel = new Label();
            ulabel.Content = unit;
            grid.Children.Add(lbl);
            grid.Children.Add(tbox);
            grid.Children.Add(ulabel);
            int row = grid.RowDefinitions.Count;
            grid.RowDefinitions.Add(new RowDefinition());
            Grid.SetColumn(lbl, 0);
            Grid.SetColumn(tbox, 1);
            Grid.SetColumn(ulabel, 2);
            Grid.SetRow(lbl, row);
            Grid.SetRow(tbox, row);
            Grid.SetRow(ulabel, row);
            return tbox;
        }

        string dialogAddStudy()
        {

            Window w = new Window();
            w.WindowStartupLocation = WindowStartupLocation.CenterScreen;
            w.Title = "New Study";
            w.SizeToContent = SizeToContent.WidthAndHeight;

            Thickness margin = new Thickness(5);

            StackPanel panel = new StackPanel();
            w.Content = panel;

            TextBlock info = new TextBlock();
            info.Text = "Add study: ";
            TextBox text = new TextBox();
            text.Width = 100;
            text.Margin = margin;
            text.Padding = new Thickness(5);

            StackPanel planPanel = new StackPanel();
            panel.Children.Add(planPanel);
            planPanel.Orientation = Orientation.Horizontal;
            planPanel.Children.Add(info);
            planPanel.Children.Add(text);

            StackPanel buttons = new StackPanel();
            buttons.Orientation = Orientation.Horizontal;
            panel.Children.Add(buttons);
            foreach (FrameworkElement e in panel.Children)
                e.Margin = margin;

            Button ok = new Button();
            buttons.Children.Add(ok);
            ok.Content = "OK";

            Button cancel = new Button();
            buttons.Children.Add(cancel);
            cancel.Content = "Cancel";

            foreach (Button b in buttons.Children)
            {
                b.Width = 100;
                b.Margin = margin;
                b.Padding = new Thickness(5);
            }

            ok.Click += (s, ev) =>
            {
                w.DialogResult = true;
                w.Close();
            };
            cancel.Click += (s, ev) =>
            {
                w.Close();
            };

            bool? res = w.ShowDialog();
            if (res == true)
            {
                return text.Text;
            }
            return "";
        }

        void writePlan(ExternalPlanSetup plan)
        {
            foreach (Beam beam in plan.Beams)
            {
				string xmlDir = studyDir + "\\xml";
				Directory.CreateDirectory(xmlDir);
                string fileName = xmlDir + "\\" + beam.Id + ".xml";
                writeXmlBeam(beam, fileName);
            }
        }

        void writeXmlBeam(Beam beam, string filepath)
        {
            XmlDocument doc = new XmlDocument();

            XmlElement root = doc.CreateElement("VarianResearchBeam");
            doc.AppendChild(root);

            root.SetAttribute("SchemaVersion", "1.0");

            XmlElement setbeam = doc.CreateElement("SetBeam");
            root.AppendChild(setbeam);

            textElement(doc, setbeam, "Id", "1");
  
            textElement(doc, setbeam, "MLCModel", "NDS120");

            XmlElement veltable = doc.CreateElement("VelTable");
            setbeam.AppendChild(veltable);
            textElement(doc, veltable, "GantryRtn", "6.0");

            XmlElement elem = doc.CreateElement("Accs");
            setbeam.AppendChild(elem);

            XmlElement controlPoints = doc.CreateElement("ControlPoints");
            setbeam.AppendChild(controlPoints);

            bool first = true;
            double gantryAngle = 0, collimatorAngle = 0, couchAngle = 0;
            //        double ttVertical = 0, ttLateral = 0, ttLongitudinal = 0;
            double x1 = 0, x2 = 0, y1 = 0, y2 = 0;
            foreach (ControlPoint cp in beam.ControlPoints)
            {
                XmlElement cpelem = doc.CreateElement("Cp");
                controlPoints.AppendChild(cpelem);
                if (first)
                {

                    XmlElement subbeam = doc.CreateElement("SubBeam");
                    cpelem.AppendChild(subbeam);
                    textElement(doc, subbeam, "Seq", "0");
                    textElement(doc, subbeam, "Name", "Beam ON");
                    textElement(doc, cpelem, "Energy", beam.EnergyModeDisplayName.ToLower());
                    
                }
                textElement(doc, cpelem, "Mu", (beam.Meterset.Value * cp.MetersetWeight).ToString("0.###"));
                if (first)
                    textElement(doc, cpelem, "DRate", "600");
                if (first || gantryAngle != cp.GantryAngle)
                {
                    gantryAngle = cp.GantryAngle;
                    rotation(doc, cpelem, "GantryRtn", gantryAngle);
                    
                }
                if (first || collimatorAngle != cp.CollimatorAngle)
                {
                    collimatorAngle = cp.CollimatorAngle;
                    rotation(doc, cpelem, "CollRtn", collimatorAngle);
                }
                /*
                 * ATTENTION: for ISO_HDMLC format, couchVrt should be couchVrtISO, same for Lat and Lng see couchRtn
                if (first)
                {
                    position(doc, cpelem, "CouchVrt", zOffset - 0.1 * beam.IsocenterPosition.y);
                    position(doc, cpelem, "CouchLat", xOffset - 0.1 * beam.IsocenterPosition.x);
                    position(doc, cpelem, "CouchLng", yOffset - 0.1 * beam.IsocenterPosition.z);
                }
                if (first || ttVertical != cp.TableTopVerticalPosition)
                {
                    ttVertical = cp.TableTopVerticalPosition;
                    position(doc, cpelem, "CouchVrt", zOffset - 0.1 * ttVertical);
                }
                if (first || ttLateral != cp.TableTopLateralPosition)
                {
                    ttLateral = cp.TableTopLateralPosition;
                    position(doc, cpelem, "CouchLat", xOffset + 0.1 * ttLateral);
                }
                if (first || ttLongitudinal != cp.TableTopLongitudinalPosition)
                {
                    ttLongitudinal = cp.TableTopLongitudinalPosition;
                    position(doc, cpelem, "CouchLng", yOffset + 0.1 * ttLongitudinal);
                }
                */
                if (first || couchAngle != cp.PatientSupportAngle)
                {
                    couchAngle = cp.PatientSupportAngle;
                    rotation(doc, cpelem, "CouchRtn", couchAngle);
                }
                if (first || y1 != cp.JawPositions.Y1)
                {
                    y1 = cp.JawPositions.Y1;
                    position(doc, cpelem, "Y1", -0.1 * y1);
                }
                if (first || y2 != cp.JawPositions.Y2)
                {
                    y2 = cp.JawPositions.Y2;
                    position(doc, cpelem, "Y2", 0.1 * y2);
                }
                if (first || x1 != cp.JawPositions.X1)
                {
                    x1 = cp.JawPositions.X1;
                    position(doc, cpelem, "X1", -0.1 * x1);
                }
                if (first || x2 != cp.JawPositions.X2)
                {
                    x2 = cp.JawPositions.X2;
                    position(doc, cpelem, "X2", 0.1 * x2);
                }

                float[,] leafs = cp.LeafPositions;
                if (leafs.Length > 0)
                {
                    XmlElement mlc = doc.CreateElement("Mlc");
                    cpelem.AppendChild(mlc);
                    textElement(doc, mlc, "ID", "1");
                    string b = join(leafs, 0, -0.1);
                    string a = join(leafs, 1, 0.1);
                    textElement(doc, mlc, "B", b);
                    textElement(doc, mlc, "A", a);
                }

                first = false;
            }

            doc.Save(filepath);
        }

        static void textElement(XmlDocument doc, XmlElement parent, string tag, string text)
        {
            XmlElement elem = doc.CreateElement(tag);
            parent.AppendChild(elem);
            elem.InnerText = text;
        }
        static void rotation(XmlDocument doc, XmlElement parent, string tag, double angle)
        {
            double a = 180.0 - angle;
            if (a < 0)
                a += 360.0;
            XmlElement elem = doc.CreateElement(tag);
            parent.AppendChild(elem);
            elem.InnerText = a.ToString("0.###");
        }
        static void position(XmlDocument doc, XmlElement parent, string tag, double pos)
        {
            XmlElement elem = doc.CreateElement(tag);
            parent.AppendChild(elem);
            elem.InnerText = pos.ToString("0.###");
        }
        static string join(float[,] leafs, int bank, double factor = 1.0)
        {
            StringBuilder sb = new StringBuilder();
            int n = leafs.GetLength(1);
            for (int i = 0; i < n; i++)
            {
                if (i > 0)
                    sb.Append(" ");
                sb.Append((factor * leafs[bank, i]).ToString("0.##"));
            }
            return sb.ToString();
        }
    }

    class Util
    {
        public static Dictionary<string, string> readPropertiesFile(string filepath)
        {
            Dictionary<string, string> prop = new Dictionary<string, string>();

            using (StreamReader r = new StreamReader(filepath))
            {
                string line;

                while ((line = r.ReadLine()) != null)
                {
                    line = line.Trim();
                    if (line.Contains('='))
                    {
                        string[] sub = line.Split('=');
                        string key = sub[0].Trim();
                        string value = sub[1].Trim();
                        prop[key] = value;
                    }
                }
            }
            return prop;
        }

        public static string[] getSubDirs(string dir)
        {
            //            Directory.CreateDirectory(dir);
            List<string> setups = new List<string>();
            if (Directory.Exists(dir))
            {
                DirectoryInfo di = new DirectoryInfo(dir);
                DirectoryInfo[] dirs = di.GetDirectories();
                foreach (DirectoryInfo d in dirs)
                    setups.Add(d.Name);
            }
            return setups.ToArray();
        }

    }

    public sealed class ProgressReporter
    {

        private readonly TaskScheduler scheduler;
        public ProgressReporter()
        {
            this.scheduler = TaskScheduler.FromCurrentSynchronizationContext();
        }

        public Task ReportProgressAsync(Action action)
        {
            return Task.Factory.StartNew(action, CancellationToken.None, TaskCreationOptions.None, this.scheduler);
        }

        public void ReportProgress(Action action)
        {
            this.ReportProgressAsync(action).Wait();
        }

    }

    class BackgroundWindow : Window
    {
        private CancellationTokenSource cancellationTokenSource;

        Label status = new Label();

        public BackgroundWindow()
        {
            WindowStartupLocation = WindowStartupLocation.CenterScreen;
            Title = "Background";
            SizeToContent = SizeToContent.WidthAndHeight;

            StackPanel panel = new StackPanel();
            Content = panel;

            status.Content = "Start";
            panel.Children.Add(status);

            Button ok = new Button();
            panel.Children.Add(ok);
            ok.Content = "OK";

            Button cancel = new Button();
            panel.Children.Add(cancel);
            cancel.Content = "Cancel";

            ok.Click += (s, ev) =>
            {
                start();
                status.Content = "Running";
            };
            cancel.Click += (s, ev) =>
            {
                cancellationTokenSource.Cancel();
            };
        }

        void start()
        {
            cancellationTokenSource = new CancellationTokenSource();
            var cancellationToken = this.cancellationTokenSource.Token;
            var progressReporter = new ProgressReporter();
            var task = Task.Factory.StartNew(() =>
            {
                for (int i = 0; i != 10; ++i)
                {
                    cancellationToken.ThrowIfCancellationRequested();
                    Thread.Sleep(500);

                    progressReporter.ReportProgress(() =>
                    {
                        this.status.Content = i;
                    });
                }
                return 42;
            });
        }
    }
}
