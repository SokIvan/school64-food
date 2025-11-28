# app.py
import streamlit as st
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
from supabase import create_client
from datetime import datetime, timedelta
import numpy as np
import os
import socket
from dotenv import load_dotenv

# Загружаем переменные окружения
load_dotenv()

# =============================================================================
# ПОДГРУЖАЕМ СТИЛИ
# =============================================================================
def load_css():
    try:
        with open('assets/style.css', 'r', encoding='utf-8') as f:
            css = f.read()
            st.markdown(f'<style>{css}</style>', unsafe_allow_html=True)
    except FileNotFoundError:
        # Fallback стили
        st.markdown("""
        <style>
            .main-header { 
                font-size: 3.5rem !important;
                text-align: center;
                margin-bottom: 1rem;
                font-weight: 700;
                background: linear-gradient(135deg, #84592B 0%, #743014 100%);
                -webkit-background-clip: text;
                -webkit-text-fill-color: transparent;
                padding: 25px;
                border: 2px solid #E8D1A7;
                border-radius: 20px;
                background-color: #F8F5F0;
                box-shadow: 0 8px 25px rgba(132, 89, 43, 0.15);
            }
            .sub-header {
                font-size: 1.8rem !important;
                text-align: center;
                margin-bottom: 3rem;
                font-weight: 300;
                color: #5D5D5D;
                font-style: italic;
            }
            .section-header {
                font-size: 2.2rem !important;
                color: #2C2C2C;
                border-left: 6px solid #84592B;
                padding-left: 20px;
                margin: 3rem 0 2rem 0;
                font-weight: 600;
                background: linear-gradient(45deg, #743014, #9D9167);
                -webkit-background-clip: text;
                -webkit-text-fill-color: transparent;
                padding: 20px;
                border-radius: 12px;
                background-color: #F8F5F0;
            }
            .info-box {
                background: linear-gradient(135deg, #FFFFFF 0%, #E8D1A7 100%);
                padding: 25px;
                border-radius: 16px;
                margin: 20px 0;
                box-shadow: 0 6px 20px rgba(132, 89, 43, 0.1);
                border: 2px solid #E8D1A7;
                border-left: 6px solid #84592B;
            }
            .info-box h3 {
                font-size: 1.8rem !important;
                margin-bottom: 15px;
            }
            .info-box p {
                font-size: 1.3rem !important;
                line-height: 1.6;
            }
            .telegram-box {
                background: linear-gradient(135deg, #FFFFFF 0%, #E8D1A7 100%);
                padding: 22px;
                border-radius: 16px;
                text-align: center;
                margin: 20px 0;
                box-shadow: 0 6px 20px rgba(132, 89, 43, 0.15);
                border: 2px solid #9D9167;
                border-left: 6px solid #84592B;
            }
            .telegram-box h4 {
                font-size: 1.6rem !important;
            }
            .telegram-box p, .telegram-box a {
                font-size: 1.3rem !important;
            }
            .metric-card {
                background: linear-gradient(135deg, #FFFFFF 0%, #F8F5F0 100%);
                padding: 25px;
                border-radius: 16px;
                text-align: center;
                box-shadow: 0 6px 20px rgba(116, 48, 20, 0.08);
                border: 2px solid #E8D1A7;
            }
            .bad-day-badge {
                background: linear-gradient(135deg, #743014 0%, #442D1C 100%);
                color: white;
                padding: 12px 20px;
                border-radius: 20px;
                font-size: 1.2rem !important;
                font-weight: 600;
                margin: 5px;
                display: inline-block;
            }
            .graph-legend {
                background: linear-gradient(135deg, #FFFFFF 0%, #F8F5F0 100%);
                padding: 20px;
                border-radius: 10px;
                margin: 15px 0;
                border: 1px solid #E8D1A7;
                font-size: 1.2rem !important;
            }
            .legend-item {
                display: flex;
                align-items: center;
                margin: 8px 0;
                font-size: 1.2rem !important;
            }
            .legend-color {
                width: 20px;
                height: 20px;
                border-radius: 3px;
                margin-right: 12px;
            }
            /* Увеличиваем шрифты в метриках */
            [data-testid="stMetricValue"] {
                font-size: 2.5rem !important;
            }
            [data-testid="stMetricLabel"] {
                font-size: 1.4rem !important;
            }
            /* Увеличиваем шрифты в селекторах */
            .stSelectbox label {
                font-size: 1.4rem !important;
            }
            .stDateInput label {
                font-size: 1.4rem !important;
            }
            /* Увеличиваем шрифты в сайдбаре */
            .css-1d391kg p {
                font-size: 1.3rem !important;
            }
        </style>
        """, unsafe_allow_html=True)

load_css()

# =============================================================================
# ОСНОВНОЙ КОД
# =============================================================================
st.set_page_config(
    page_title="Школа 64 - Анализ питания",
    page_icon="🏫",
    layout="wide",
    initial_sidebar_state="expanded"
)

# =============================================================================
# ПОДКЛЮЧЕНИЕ К SUPABASE
# =============================================================================
@st.cache_resource
def init_supabase():
    try:
        client = create_client(
            supabase_url=os.getenv("SUPABASE_URL"),
            supabase_key=os.getenv("SUPABASE_KEY")
        )
        return client
    except Exception as e:
        st.error(f"Ошибка подключения к базе данных: {e}")
        return None

@st.cache_data(ttl=300)
def load_real_data(_supabase):
    """Загружает реальные данные из базы"""
    try:
        surveys_response = _supabase.table("surveys").select("*").execute()
        users_response = _supabase.table("users").select("*").execute()
        meal_ratings_response = _supabase.table("meal_ratings").select("*").execute()
        meal_comments_response = _supabase.table("meal_comments").select("*").execute()
        
        surveys_df = pd.DataFrame(surveys_response.data)
        users_df = pd.DataFrame(users_response.data)
        meal_ratings_df = pd.DataFrame(meal_ratings_response.data)
        meal_comments_df = pd.DataFrame(meal_comments_response.data)
        
        return {
            'surveys': surveys_df,
            'users': users_df,
            'meal_ratings': meal_ratings_df,
            'meal_comments': meal_comments_df
        }
    except Exception as e:
        st.error(f"Ошибка загрузки данных: {e}")
        return None

def normalize_class_name(class_name):
    """Нормализует названия классов - оставляем только 10А и 11А"""
    if pd.isna(class_name):
        return None
    
    class_name = str(class_name).strip().upper()
    
    if class_name in ['10А', '10A', '10А']:
        return '10А'
    elif class_name in ['11А', '11A', '11А']:
        return '11А'
    else:
        return None

def filter_and_normalize_classes(merged_df):
    """Нормализует классы и оставляет только 10А и 11А"""
    if merged_df.empty or 'class' not in merged_df.columns:
        return merged_df
    
    merged_df['class_normalized'] = merged_df['class'].apply(normalize_class_name)
    filtered_df = merged_df[merged_df['class_normalized'].notna()].copy()
    filtered_df['class'] = filtered_df['class_normalized']
    filtered_df = filtered_df.drop('class_normalized', axis=1)
    
    return filtered_df

# =============================================================================
# НОВЫЕ ФУНКЦИИ ДЛЯ ГРАФИКОВ В ПОСТЕЛЬНЫХ ТОНАХ
# =============================================================================
def get_bad_days_stats(data):
    """Находит дни с плохими оценками (средняя оценка < 3.0)"""
    if data.empty:
        return []
    
    daily_stats = data.groupby('date').agg({
        'overall_satisfaction': ['mean', 'count']
    }).round(2)
    daily_stats.columns = ['avg_rating', 'survey_count']
    daily_stats = daily_stats.reset_index()
    
    # Дни с плохими оценками
    bad_days = daily_stats[daily_stats['avg_rating'] < 3.0]
    
    return bad_days.to_dict('records')

def create_daily_avg_ratings_chart(data, selected_class=None):
    """График средних оценок по дням (усреднение по 3 блюдам)"""
    if data.empty:
        return None
    
    # Фильтрация по классу
    if selected_class and selected_class != "Все классы":
        filtered_data = data[data['class'] == selected_class]
        title = f'Средние оценки по дням - {selected_class}'
    else:
        filtered_data = data
        title = 'Средние оценки по дням'
    
    # Группируем по дате и считаем среднюю оценку
    daily_stats = filtered_data.groupby('date').agg({
        'overall_satisfaction': 'mean'
    }).round(2).reset_index()
    
    fig = px.line(
        daily_stats,
        x='date',
        y='overall_satisfaction',
        title=title,
        labels={'date': 'Дата', 'overall_satisfaction': 'Средняя оценка'},
        color_discrete_sequence=['#84592B']
    )
    
    # УВЕЛИЧИВАЕМ ШРИФТЫ В ГРАФИКАХ
    fig.update_layout(
        font=dict(size=18),  # Увеличиваем базовый размер шрифта
        title_font_size=24,
        xaxis=dict(
            tickformat='%d.%m.%Y',
            title_font_size=20,
            tickfont_size=18
        ),
        yaxis=dict(
            title_font_size=20,
            tickfont_size=18
        ),
        plot_bgcolor='rgba(0,0,0,0)',
        paper_bgcolor='rgba(0,0,0,0)',
        hovermode='x unified',
        showlegend=False
    )
    
    fig.update_traces(
        line=dict(width=4),
        marker=dict(size=10, color='#743014')
    )
    
    # Добавляем горизонтальную линию для порога "плохого дня"
    fig.add_hline(y=3.0, line_dash="dash", line_color="#743014", 
                 annotation_text="Порог низкой оценки", 
                 annotation_position="bottom right",
                 annotation_font_size=16)
    
    return fig

def create_rating_distribution(data, selected_class=None):
    """Гистограмма распределения оценок с разными цветами"""
    if selected_class and selected_class != "Все классы":
        filtered_data = data[data['class'] == selected_class]
        title = f'Распределение оценок - {selected_class}'
    else:
        filtered_data = data
        title = 'Распределение общих оценок'
    
    if filtered_data.empty:
        return None
    
    # ФИКСИРОВАННАЯ ЦВЕТОВАЯ ПАЛИТРА ДЛЯ КАЖДОЙ ОЦЕНКИ
    rating_colors = {
        1: '#442D1C',  # Самый темный для низкой оценки
        2: '#743014',  
        3: '#84592B',  
        4: '#9D9167',  
        5: '#E8D1A7'   # Самый светлый для высокой оценки
    }
    
    # Создаем гистограмму с помощью go.Bar для индивидуальных цветов
    rating_counts = filtered_data['overall_satisfaction'].value_counts().sort_index()
    
    # Создаем списки для данных
    ratings = []
    counts = []
    colors = []
    
    for rating in sorted(rating_counts.index):
        ratings.append(f'{rating} ⭐')
        counts.append(rating_counts[rating])
        colors.append(rating_colors[rating])
    
    fig = go.Figure(data=[go.Bar(
        x=ratings,
        y=counts,
        marker_color=colors,
        hovertemplate='<b>Оценка: %{x}</b><br>Количество: %{y}<extra></extra>'
    )])
    
    # УВЕЛИЧИВАЕМ ШРИФТЫ В ГРАФИКАХ
    fig.update_layout(
        title=title,
        font=dict(size=18),
        title_font_size=24,
        xaxis=dict(
            title='Оценка',
            title_font_size=20,
            tickfont_size=18
        ),
        yaxis=dict(
            title='Количество оценок',
            title_font_size=20,
            tickfont_size=18
        ),
        plot_bgcolor='rgba(0,0,0,0)',
        paper_bgcolor='rgba(0,0,0,0)',
        bargap=0.1,
    )
    
    return fig

def create_class_comparison(data):
    """Сравнение средних оценок по классам"""
    if data.empty:
        return None
        
    class_stats = data.groupby('class')['overall_satisfaction'].agg(['mean', 'count']).reset_index()
    class_stats = class_stats[class_stats['count'] > 0]
    
    # Постельная цветовая шкала
    fig = px.bar(
        class_stats,
        x='class',
        y='mean',
        title='Сравнение средних оценок по классам',
        color='mean',
        color_continuous_scale=['#E8D1A7', '#9D9167', '#84592B', '#743014'],
        labels={'class': 'Класс', 'mean': 'Средняя оценка'}
    )
    
    # УВЕЛИЧИВАЕМ ШРИФТЫ В ГРАФИКАХ
    fig.update_layout(
        font=dict(size=18),
        title_font_size=24,
        xaxis=dict(
            title_font_size=20,
            tickfont_size=18
        ),
        yaxis=dict(
            title_font_size=20,
            tickfont_size=18
        ),
        coloraxis_showscale=False,
        plot_bgcolor='rgba(0,0,0,0)',
        paper_bgcolor='rgba(0,0,0,0)',
    )
    return fig

def get_eating_statistics(data):
    """Статистика по питанию в школе - подсчет анкет"""
    if data.empty:
        return 0, 0, 0
    
    # Считаем по всем анкетам, а не по уникальным пользователям
    eats_at_school_count = data['eats_at_school'].sum()
    not_eat_at_school_count = len(data) - eats_at_school_count
    total_entries = len(data)
    
    return eats_at_school_count, not_eat_at_school_count, total_entries

def get_daily_eating_statistics(data):
    """Статистика питания по дням - подсчет анкет"""
    if data.empty:
        return pd.DataFrame()
    
    # Группируем по дате и считаем анкеты
    daily_stats = data.groupby('date').agg({
        'eats_at_school': ['count', 'sum']  # Всего анкет и питающихся
    }).reset_index()
    
    daily_stats.columns = ['date', 'total_surveys', 'eats_at_school_count']
    daily_stats['not_eat_count'] = daily_stats['total_surveys'] - daily_stats['eats_at_school_count']
    daily_stats['eat_percentage'] = (daily_stats['eats_at_school_count'] / daily_stats['total_surveys'] * 100).round(1)
    
    return daily_stats

def create_meal_ratings_pie_charts(meal_ratings_df, surveys_df, users_df, selected_class=None, date_range=None):
    """Три круговые диаграммы оценок по типам блюд"""
    
    # Объединяем данные
    merged_ratings = meal_ratings_df.merge(
        surveys_df[['id', 'telegram_id', 'date']], 
        left_on='survey_id', 
        right_on='id'
    ).merge(
        users_df[['telegram_id', 'class']], 
        on='telegram_id'
    )
    
    # Нормализуем и фильтруем классы
    merged_ratings = filter_and_normalize_classes(merged_ratings)
    
    # Применяем фильтры
    if selected_class and selected_class != "Все классы":
        merged_ratings = merged_ratings[merged_ratings['class'] == selected_class]
    
    if date_range and len(date_range) == 2:
        start_date, end_date = date_range
        merged_ratings = merged_ratings[
            (merged_ratings['date'] >= pd.to_datetime(start_date)) & 
            (merged_ratings['date'] <= pd.to_datetime(end_date))
        ]
    
    if merged_ratings.empty:
        return None
    
    # ФИКСИРОВАННАЯ ЦВЕТОВАЯ ПАЛИТРА ДЛЯ ОЦЕНОК (от светлого к темному)
    rating_colors = {
        5: '#E8D1A7',  # Самый светлый - Golden Batter
        4: '#9D9167',  # Olive Harvest  
        3: '#84592B',  # Toasted Caramel
        2: '#743014',  # Spiced Wine
        1: '#442D1C'   # Самый темный - Couhide Cocoa
    }
    
    # Создаем три диаграммы
    meal_types = ['первое', 'второе', 'напиток']
    figs = []
    
    for meal_type in meal_types:
        meal_data = merged_ratings[merged_ratings['meal_type'] == meal_type]
        
        if meal_data.empty:
            fig = go.Figure()
            fig.add_annotation(text="Нет данных", x=0.5, y=0.5, showarrow=False, font=dict(size=20))
            fig.update_layout(
                title=f'{meal_type.title()}',
                plot_bgcolor='rgba(0,0,0,0)',
                paper_bgcolor='rgba(0,0,0,0)',
                font=dict(size=18)
            )
        else:
            rating_counts = meal_data['rating'].value_counts().sort_index(ascending=False)  # Сортируем от 5 к 1
            
            # Создаем данные для диаграммы с фиксированными цветами
            labels = []
            values = []
            colors = []
            
            for rating in sorted(rating_counts.index, reverse=True):  # От 5 к 1
                labels.append(f'{rating} ⭐')
                values.append(rating_counts[rating])
                colors.append(rating_colors[rating])
            
            fig = go.Figure(data=[go.Pie(
                labels=labels,
                values=values,
                marker=dict(colors=colors),
                hole=0.3,
                sort=False,  # Сохраняем порядок от 5 к 1
                textfont=dict(size=16)  # Увеличиваем шрифт в диаграмме
            )])
            
            fig.update_layout(
                title=f'{meal_type.title()}',
                title_font_size=22,
                plot_bgcolor='rgba(0,0,0,0)',
                paper_bgcolor='rgba(0,0,0,0)',
                showlegend=True,
                font=dict(size=16),
                legend=dict(
                    orientation="h",
                    yanchor="bottom",
                    y=-0.2,
                    xanchor="center",
                    x=0.5,
                    font=dict(size=16)
                )
            )
        
        figs.append(fig)
    
    return figs

def create_daily_surveys_chart(surveys_df, users_df, selected_class=None, date_range=None):
    """График количества анкет по дням"""
    # Объединяем данные
    merged_data = surveys_df.merge(
        users_df[['telegram_id', 'class']], 
        on='telegram_id',
        how='left'
    )
    
    # Нормализуем и фильтруем классы
    merged_data = filter_and_normalize_classes(merged_data)
    
    if merged_data.empty:
        return None
    
    # Применяем фильтры
    filtered_data = merged_data.copy()
    if selected_class and selected_class != "Все классы":
        filtered_data = filtered_data[filtered_data['class'] == selected_class]
    
    if date_range and len(date_range) == 2:
        start_date, end_date = date_range
        filtered_data = filtered_data[
            (filtered_data['date'] >= pd.to_datetime(start_date)) & 
            (filtered_data['date'] <= pd.to_datetime(end_date))
        ]
    
    if filtered_data.empty:
        return None
    
    # КОНТРАСТНЫЕ ЦВЕТА для классов
    class_colors = {'10А': "#B39474", '11А': '#743014'}  # Темно-коричневый и темно-красный
    
    # Группируем по дате и классу
    if selected_class == "Все классы":
        daily_stats = filtered_data.groupby(['date', 'class']).size().reset_index(name='count')
        
        fig = px.line(
            daily_stats,
            x='date',
            y='count',
            color='class',
            title='Активность голосований по дням',
            color_discrete_map=class_colors,
            labels={'date': 'Дата', 'count': 'Количество анкет', 'class': 'Класс'},
            markers=True
        )
        
        # Увеличиваем контрастность линий
        fig.update_traces(
            line=dict(width=4),
            marker=dict(size=10)
        )
        
    else:
        daily_stats = filtered_data.groupby('date').size().reset_index(name='count')
        
        # Используем контрастный цвет для одиночного класса
        single_class_color = '#84592B' if selected_class == '10А' else '#743014'
        
        fig = px.line(
            daily_stats,
            x='date',
            y='count',
            title=f'Активность голосований - {selected_class}',
            color_discrete_sequence=[single_class_color],
            labels={'date': 'Дата', 'count': 'Количество анкет'},
            markers=True
        )
        fig.update_traces(
            line=dict(width=4),
            marker=dict(size=10)
        )
    
    # УВЕЛИЧИВАЕМ ШРИФТЫ В ГРАФИКАХ
    fig.update_layout(
        font=dict(size=18),
        title_font_size=24,
        xaxis=dict(
            tickformat='%d.%m.%Y',
            title_font_size=20,
            tickfont_size=18
        ),
        yaxis=dict(
            title_font_size=20,
            tickfont_size=18
        ),
        showlegend=(selected_class == "Все классы"),
        plot_bgcolor='rgba(0,0,0,0)',
        paper_bgcolor='rgba(0,0,0,0)',
        legend=dict(
            bgcolor='rgba(255,255,255,0.8)',
            bordercolor='#E8D1A7',
            borderwidth=1,
            font=dict(size=16)
        )
    )
    
    return fig

# =============================================================================
# ОСНОВНОЕ ПРИЛОЖЕНИЕ
# =============================================================================
def main():
    # ЗАГОЛОВОК С ОПИСАНИЕМ
    st.markdown('<h1 class="main-header">Школа 64</h1>', unsafe_allow_html=True)
    st.markdown('<div class="sub-header">Анализ качества питания в школьной столовой</div>', unsafe_allow_html=True)
    
    # ИНФОРМАЦИОННЫЙ БЛОК
    with st.container():
        col1, col2 = st.columns([3, 1])
        
        with col1:
            st.markdown("""
            <div class="info-box">
                <h3>О дашборде</h3>
                <p>Этот дашборд анализирует отзывы учащихся о питании в школьной столовой. 
                Данные собираются через Telegram-бота, где ученики ежедневно оценивают качество блюд.</p>
            </div>
            """, unsafe_allow_html=True)
        
        with col2:
            st.markdown("""
            <div class="telegram-box">
                <h4>Telegram-бот</h4>
                <p>Присоединяйтесь к оценке питания!</p>
                <a href="https://t.me/foodschool64_bot" target="_blank" style="color: white; text-decoration: none;">
                    <b>@foodschool64_bot</b>
                </a>
            </div>
            """, unsafe_allow_html=True)
    
    # Инициализация Supabase
    supabase = init_supabase()
    if not supabase:
        st.error("Не удалось подключиться к базе данных. Проверьте файл .env")
        return
    
    # Загрузка данных
    with st.spinner('Загрузка данных...'):
        data_dict = load_real_data(supabase)
    
    if not data_dict:
        return
    
    # Обработка данных
    surveys_df = data_dict['surveys']
    users_df = data_dict['users']
    
    merged_df = surveys_df.merge(users_df, on='telegram_id', how='left')
    merged_df = filter_and_normalize_classes(merged_df)
    
    if not merged_df.empty:
        merged_df['date'] = pd.to_datetime(merged_df['date'])
        surveys_df['date'] = pd.to_datetime(surveys_df['date'])
    
    # =========================================================================
    # БОКОВАЯ ПАНЕЛЬ - ФИЛЬТРЫ
    # =========================================================================
    with st.sidebar:
        st.markdown("### Панель управления")
        st.markdown("---")
        
        # Выбор класса
        available_classes = ["Все классы"]
        if not merged_df.empty and 'class' in merged_df.columns:
            class_counts = merged_df['class'].value_counts()
            for cls, count in class_counts.items():
                available_classes.append(f"{cls} ({count})")
        
        selected_class = st.selectbox("**Выберите класс:**", available_classes)
        
        if selected_class != "Все классы":
            selected_class = selected_class.split(' (')[0]
        
        # Выбор даты
        available_dates = []
        if not merged_df.empty and 'date' in merged_df.columns:
            available_dates = sorted(merged_df['date'].dt.date.unique())
        
        if available_dates:
            min_date = min(available_dates)
            max_date = max(available_dates)
            
            date_range = st.date_input(
                "**Период анализа:**",
                value=(min_date, max_date),
                min_value=min_date,
                max_value=max_date
            )
            
            if date_range and len(date_range) == 1:
                date_range = (date_range[0], max_date)
        else:
            date_range = None
        
        # Применяем фильтры
        filtered_df = merged_df.copy()
        if selected_class and selected_class != "Все классы":
            filtered_df = filtered_df[filtered_df['class'] == selected_class]
        
        if date_range and len(date_range) == 2:
            start_date, end_date = date_range
            filtered_df = filtered_df[
                (filtered_df['date'] >= pd.to_datetime(start_date)) & 
                (filtered_df['date'] <= pd.to_datetime(end_date))
            ]
        
        # Статистика
        st.markdown("---")
        st.markdown("### Статистика")
        st.metric("Всего анкет", len(filtered_df))
        if not filtered_df.empty and 'overall_satisfaction' in filtered_df.columns:
            avg_rating = filtered_df['overall_satisfaction'].mean()
            st.metric("Средняя оценка", f"{avg_rating:.1f}")
    
    # =========================================================================
    # НОВЫЙ РАЗДЕЛ: ДНИ С ПЛОХИМИ ОЦЕНКАМИ
    # =========================================================================
    if not filtered_df.empty:
        bad_days = get_bad_days_stats(filtered_df)
        
        if bad_days:
            st.markdown('<div class="section-header">Дни с низкими оценками</div>', unsafe_allow_html=True)
            
            st.warning("Обнаружены дни с низкими средними оценками питания:")
            
            cols = st.columns(3)
            for idx, day in enumerate(bad_days[:3]):  # Показываем максимум 3 худших дня
                with cols[idx % 3]:
                    st.markdown(f"""
                    <div class="bad-day-badge">
                        <strong>{day['date'].strftime('%d.%m.%Y')}</strong><br>
                        Оценка: {day['avg_rating']}<br>
                        Анкет: {day['survey_count']}
                    </div>
                    """, unsafe_allow_html=True)
    
    # =========================================================================
    # ОСНОВНЫЕ МЕТРИКИ С ДОПОЛНИТЕЛЬНОЙ ИНФОРМАЦИЕЙ
    # =========================================================================
    st.markdown('<div class="section-header">Общая статистика</div>', unsafe_allow_html=True)
    
    col1, col2, col3, col4 = st.columns(4)
    
    with col1:
        total_surveys = len(filtered_df)
        st.metric("Всего оценок", total_surveys)
        st.markdown('<div class="graph-legend"><div class="legend-item"><div class="legend-color" style="background-color: #84592B;"></div><span>Общее количество заполненных анкет</span></div></div>', unsafe_allow_html=True)
    
    with col2:
        if not filtered_df.empty and 'overall_satisfaction' in filtered_df.columns:
            avg_rating = filtered_df['overall_satisfaction'].mean()
            st.metric("Средняя оценка", f"{avg_rating:.1f}")
            st.markdown('<div class="graph-legend"><div class="legend-item"><div class="legend-color" style="background-color: #743014;"></div><span>Средняя оценка за весь период</span></div></div>', unsafe_allow_html=True)
        else:
            st.metric("Средняя оценка", "0.0")
    
    with col3:
        if not filtered_df.empty and 'overall_satisfaction' in filtered_df.columns:
            max_rating = filtered_df['overall_satisfaction'].max()
            st.metric("Максимальная оценка", int(max_rating))
            st.markdown('<div class="graph-legend"><div class="legend-item"><div class="legend-color" style="background-color: #9D9167;"></div><span>Наивысшая полученная оценка</span></div></div>', unsafe_allow_html=True)
        else:
            st.metric("Максимальная оценка", "0")
    
    with col4:
        if not filtered_df.empty and 'class' in filtered_df.columns:
            unique_classes = filtered_df['class'].nunique()
            st.metric("Активных классов", unique_classes)
            st.markdown('<div class="graph-legend"><div class="legend-item"><div class="legend-color" style="background-color: #442D1C;"></div><span>Количество классов, участвующих в оценке</span></div></div>', unsafe_allow_html=True)
        else:
            st.metric("Активных классов", "0")
    
    # ДОПОЛНИТЕЛЬНАЯ СТАТИСТИКА ПО ПИТАНИЮ
    st.markdown('<div class="section-header">Статистика питания</div>', unsafe_allow_html=True)
    
    # Получаем статистику по пользователям
    eats_count, not_eat_count, total_with_data = get_eating_statistics(filtered_df)
    
    col1, col2, col3 = st.columns(3)
    
    with col1:
        if total_with_data > 0:
            percentage = (eats_count / total_with_data) * 100
            st.metric("Питались при подаче анкеты", f"{eats_count} чел. ({percentage:.1f}%)")
            st.markdown('<div class="graph-legend"><div class="legend-item"><div class="legend-color" style="background-color: #84592B;"></div><span>Количество пользователей, которые питаются в столовой</span></div></div>', unsafe_allow_html=True)
        else:
            st.metric("Питаются в школе", "Нет данных")
    
    with col2:
        if total_with_data > 0:
            percentage = (not_eat_count / total_with_data) * 100
            st.metric("Не питались при подаче анкеты", f"{not_eat_count} чел. ({percentage:.1f}%)")
            st.markdown('<div class="graph-legend"><div class="legend-item"><div class="legend-color" style="background-color: #743014;"></div><span>Количество пользователей, которые не питаются в столовой</span></div></div>', unsafe_allow_html=True)
        else:
            st.metric("Не питаются в школе", "Нет данных")
    
    with col3:
        total_surveys = len(filtered_df)
        st.metric("Всего анкет", f"{total_surveys} шт.")
        st.markdown('<div class="graph-legend"><div class="legend-item"><div class="legend-color" style="background-color: #9D9167;"></div><span>Общее количество заполненных анкет за период</span></div></div>', unsafe_allow_html=True)    
    
    # =========================================================================
    # ГРАФИКИ
    # =========================================================================
    if not filtered_df.empty:
        # НОВЫЙ ГРАФИК: СРЕДНИЕ ОЦЕНКИ ПО ДНЯМ
        st.markdown('<div class="section-header">Динамика средних оценок по дням</div>', unsafe_allow_html=True)
        fig_daily_avg = create_daily_avg_ratings_chart(filtered_df, selected_class)
        if fig_daily_avg:
            st.plotly_chart(fig_daily_avg, width='stretch')
            st.markdown("""
            <div class="graph-legend">
                <strong>Пояснение к графику:</strong><br>
                На графике показана средняя оценка питания за каждый день. Пунктирная линия показывает порог низкой оценки (3.0). 
                Дни ниже этого порога требуют особого внимания.
            </div>
            """, unsafe_allow_html=True)
        
        # Первая строка графиков
        col1, col2 = st.columns(2)
        
        with col1:
            fig1 = create_rating_distribution(filtered_df, selected_class)
            if fig1:
                st.plotly_chart(fig1, width='stretch')
                st.markdown('<div class="graph-legend"><div class="legend-item"><div class="legend-color" style="background-color: #84592B;"></div><span>Распределение оценок по 5-балльной шкале</span></div></div>', unsafe_allow_html=True)
        
        with col2:
            fig2 = create_class_comparison(filtered_df)
            if fig2:
                st.plotly_chart(fig2, width='stretch')
                st.markdown('<div class="graph-legend"><div class="legend-item"><div class="legend-color" style="background-color: #9D9167;"></div><span>Сравнение средней оценки между классами</span></div></div>', unsafe_allow_html=True)
        
        # Вторая строка графиков
        st.markdown('<div class="section-header">Оценки по типам блюд</div>', unsafe_allow_html=True)
        
        pie_charts = create_meal_ratings_pie_charts(
            data_dict['meal_ratings'], 
            data_dict['surveys'], 
            data_dict['users'],
            selected_class,
            date_range
        )
        
        if pie_charts:
            col1, col2, col3 = st.columns(3)
            with col1:
                st.plotly_chart(pie_charts[0], width='stretch')
                st.markdown('<div class="graph-legend" style="text-align: center;">Распределение оценок для первых блюд</div>', unsafe_allow_html=True)
            with col2:
                st.plotly_chart(pie_charts[1], width='stretch')
                st.markdown('<div class="graph-legend" style="text-align: center;">Распределение оценок для вторых блюд</div>', unsafe_allow_html=True)
            with col3:
                st.plotly_chart(pie_charts[2], width='stretch')
                st.markdown('<div class="graph-legend" style="text-align: center;">Распределение оценок для напитков</div>', unsafe_allow_html=True)
        
        # Третий график
        st.markdown('<div class="section-header">Активность голосований</div>', unsafe_allow_html=True)
        
        fig_daily = create_daily_surveys_chart(
            data_dict['surveys'], 
            data_dict['users'],
            selected_class,
            date_range
        )
        if fig_daily:
            st.plotly_chart(fig_daily, width='stretch')
            st.markdown("""
            <div class="graph-legend">
                <strong>Пояснение к графику:</strong><br>
                График показывает количество заполненных анкет по дням. Это помогает оценить активность учащихся в оценке питания.
            </div>
            """, unsafe_allow_html=True)
    
    else:
        st.warning("Нет данных для отображения с выбранными фильтрами")
    
    # =========================================================================
    # ФУТЕР
    # =========================================================================
    st.markdown("---")
    col1, col2, col3 = st.columns([1, 2, 1])
    
    with col2:
        st.markdown("""
        <div style="text-align: center; color: #5D5D5D; font-size: 1.2rem;">
            <p>Дашборд анализа школьного питания • Школа 64</p>
            <p>Данные собираются через <a href="https://t.me/foodschool64_bot" target="_blank">Telegram-бота</a></p>
        </div>
        """, unsafe_allow_html=True)

if __name__ == "__main__":
    main()