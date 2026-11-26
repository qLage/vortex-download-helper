// An isolated WPF test window. It never contacts a website or downloads files.
using System;
using System.IO;
using System.Windows;
using System.Windows.Automation;
using System.Windows.Controls;
using System.Windows.Threading;
internal static class Fixture {
    [STAThread] private static void Main(string[] args) {
        string directory=args[0], control=Path.Combine(directory,"fixture-control.txt"), countPath=Path.Combine(directory,"clicks.txt");
        int count=0, mod=1; string previous="";
        Window window=new Window {Title="Vortex Helper TEST — no downloads",Width=560,Height=350,Topmost=false};
        GroupBox group=new GroupBox();
        StackPanel dialog=new StackPanel {Margin=new Thickness(24)};
        AutomationProperties.SetAutomationId(group,"free-user-dl-dialog");
        group.Content=dialog;
        dialog.Children.Add(new TextBlock {Text="Download mod"});
        TextBlock title=new TextBlock {Text="Fixture Mod 1",FontSize=22};dialog.Children.Add(title);
        dialog.Children.Add(new TextBlock {Text="by Fixture Author"});
        TextBlock progress=new TextBlock {Text="1/3"};dialog.Children.Add(progress);
        Button button=new Button {Content="Download manually",Margin=new Thickness(0,20,0,0),Height=45};
        AutomationProperties.SetAutomationId(button,"download-mod-button");dialog.Children.Add(button);
        button.Click+=delegate {count++;File.WriteAllText(countPath,count.ToString());};
        window.Content=group;
        DispatcherTimer timer=new DispatcherTimer {Interval=TimeSpan.FromMilliseconds(100)};
        timer.Tick+=delegate {
            if(!File.Exists(control))return;
            string command=File.ReadAllText(control);
            if(command==previous)return;previous=command;
            if(command.StartsWith("move"))button.Margin=new Thickness(100,35,0,0);
            if(command.StartsWith("next")){mod++;title.Text="Fixture Mod "+mod;progress.Text=mod+"/3";}
        };
        window.Loaded+=delegate {File.WriteAllText(countPath,"0");File.WriteAllText(Path.Combine(directory,"ready"),"ready");timer.Start();};
        new Application().Run(window);
    }
}
